#!/usr/bin/python
from __future__ import print_function
import os
import sys
import time
import datetime
import random
import subprocess
import threading
import re
import filecmp
import shutil
import argparse
import uuid
import common_functions as cf
import profiler

if sys.version_info >= (3, 0):
    import configparser  # python 3
else:
    import ConfigParser  # python 2

"""
Start the gdb script
"""


class RunGDB(threading.Thread):
    section = None
    conf = None
    unique_id = None

    def __init__(self, section, conf, unique_id):
        threading.Thread.__init__(self)
        self.section = section
        self.unique_id = unique_id
        self.conf = conf

    def run(self):
        start_cmd = self.conf.get(self.section,
                                  "gdbExecName") + " -n -q -batch -x " + "/tmp/flip-" + self.unique_id + ".py"
        os.system(start_cmd)


"""
Check if app stops execution (otherwise kill it after a time)
"""


def finish(section, conf, logging, timestamp_start):
    is_hang = False
    now = int(time.time())

    # Wait 2 times the normal duration of the program before killing it
    max_wait_time = conf.getfloat(section, "maxWaitTime")
    gdb_exec_name = conf.get(section, "gdbExecName")
    check_running = "ps -e | grep -i " + gdb_exec_name
    kill_strs = conf.get(section, "killStrs")

    while (now - timestamp_start) < (max_wait_time * 2):
        time.sleep(max_wait_time / 10)

        # Check if the gdb is still running, if not, stop waiting
        proc = subprocess.Popen(check_running, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()

        if not re.search(gdb_exec_name, str(out)):
            logging.debug("Process " + str(gdb_exec_name) + " not running, out:" + str(out))
            logging.debug("check command: " + check_running)
            break
        now = int(time.time())

    # check execution finished before or after waitTime
    if (now - timestamp_start) < max_wait_time * 2:
        logging.info("Execution finished before waitTime")
    else:
        logging.info("Execution did not finish before waitTime")
        is_hang = True

    logging.debug("now: " + str(now))
    logging.debug("timestampStart: " + str(timestamp_start))

    # Kill all the processes to make sure the machine is clean for another test
    for k in kill_strs.split(";"):
        proc = subprocess.Popen(k, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        logging.debug("kill cmd: " + k)
        if out is not None:
            logging.debug("kill cmd, shell stdout: " + str(out))
        if err is not None:
            logging.error("kill cmd, shell stderr: " + str(err))

    return is_hang


"""
Copy the logs and output(if fault not masked) to a selected folder
"""


def save_output(section, is_sdc, is_hang, conf, logging):
    output_file = conf.get(section, "outputFile")
    flip_log_file = "/tmp/carolfi-flipvalue-" + unique_id + ".log"

    fi_succ = False
    if os.path.isfile(flip_log_file):
        fp = open(flip_log_file, "r")
        content = fp.read()
        if re.search("Fault Injection Successful", content):
            fi_succ = True
        fp.close()

    dt = datetime.datetime.fromtimestamp(time.time())
    ymd = dt.strftime('%Y_%m_%d')
    ymdhms = dt.strftime('%Y_%m_%d_%H_%M_%S')
    ymdhms = unique_id + "-" + ymdhms
    dir_d_t = os.path.join(ymd, ymdhms)
    masked = False
    if not fi_succ:
        cp_dir = os.path.join('logs', section, 'failed-injection', dir_d_t)
        logging.summary(section + " - Fault Injection Failed")
    elif is_hang:
        cp_dir = os.path.join('logs', section, 'hangs', dir_d_t)
        logging.summary(section + " - Hang")
    elif is_sdc:
        cp_dir = os.path.join('logs', section, 'sdcs', dir_d_t)
        logging.summary(section + " - SDC")
    elif not os.path.isfile(output_file):
        cp_dir = os.path.join('logs', section, 'noOutputGenerated', dir_d_t)
        logging.summary(section + " - NoOutputGenerated")
    else:
        cp_dir = os.path.join('logs', section, 'masked', dir_d_t)
        logging.summary(section + " - Masked")
        masked = True

    if not os.path.isdir(cp_dir):
        os.makedirs(cp_dir)

    shutil.move(flip_log_file, cp_dir)
    shutil.move(gdb_fi_log_file, cp_dir)
    if os.path.isfile(output_file) and (not masked) and fi_succ:
        shutil.move(output_file, cp_dir)


"""
Pre execution commands
"""


def pre_execution(section, conf):
    try:
        script = conf.get(section, "preExecScript")
        if script != "":
            os.system(script)
        return
    except:
        return


"""
Pos execution commands
"""


def pos_execution(section, conf):
    try:
        script = conf.get(section, "posExecScript")
        if script != "":
            os.system(script)
        return
    except:
        return


"""
Check output files for SDCs
"""


def check_sdcs(section, conf, logging):
    goldFile = conf.get(section, "goldFile")
    outputFile = conf.get(section, "outputFile")
    if not os.path.isfile(outputFile):
        logging.error("outputFile not found: " + str(outputFile))
    if os.path.isfile(goldFile) and os.path.isfile(outputFile):
        return (not filecmp.cmp(goldFile, outputFile, shallow=False))
    else:
        return False

"""
Generate config file for the gdb flip_value script
"""


def gen_conf_file(gdb_init_strings, debug, unique_id, valid_block, valid_thread, bits_to_flip, fault_model,
                  injection_site):
    if sys.version_info >= (3, 0):
        fconf = configparser.SafeConfigParser()
    else:
        fconf = ConfigParser.SafeConfigParser()

    fconf.set("DEFAULT", "flipLogFile", "/tmp/carolfi-flipvalue-" + unique_id + ".log")
    fconf.set("DEFAULT", "debug", debug)
    fconf.set("DEFAULT", "gdbInitStrings", gdb_init_strings)
    fconf.set("DEFAULT", "faultModel", fault_model)
    fconf.set("DEFAULT", "injectionSite", injection_site)
    fconf.set("DEFAULT", "validThread", valid_thread)
    fconf.set("DEFAULT", "validBlock", valid_block)
    fconf.set("DEFAULT", "bits_to_flip", bits_to_flip)

    fp = open("/tmp/flip-" + unique_id + ".conf", "w")
    fconf.write(fp)
    fp.close()


"""
Generate the gdb flip_value script
"""


def gen_flip_script(unique_id):
    fp = open("flip_value.py", "r")
    pscript = fp.read()
    fp.close()
    fp = open("/tmp/flip-" + unique_id + ".py", "w")

    fp.write(pscript.replace("<conf-location>", "/tmp/flip-" + unique_id + ".conf"))
    fp.write(pscript.replace("<home-location>", "/home/carol/carol-fi"))
    fp.close()
    os.chmod("/tmp/flip-" + unique_id + ".py", 0775)


"""
Select a valid stop address
from the file created in the profiler
step
"""


def get_valid_address(addresses):
    m = None
    registers = []
    instruction = ''
    address = ''
    byte_location = ''

    # search for a valid instruction
    while not m:
        element = random.randrange((len(addresses) - 1) / 2, len(addresses) - 1)
        instruction_line = addresses[element]

        expression = ".*([0-9a-fA-F][xX][0-9a-fA-F]+) (\S+):[ \t\n\r\f\v]*(\S+)[ ]*(\S+)"

        for i in [1, 3, 4, 5]:
            # INSTRUCTION R1, R2...
            # 0x0000000000b418e8 <+40>: MOV R4, R2...
            expression += ",[ ]*(\S+)"
            m = re.match(expression + ".*", instruction_line)

            if m:
                address = m.group(1)
                byte_location = m.group(2)
                instruction = m.group(3)
                registers.extend([m.group(3 + t) for t in range(0, i)])
                break

        if not m:
            print("it is stoped here:", instruction_line)
        else:
            print("it choose something:", instruction_line)

    return registers, instruction, address, byte_location


"""

"""


def get_valid_thread(threads):
    element = random.randrange(0, len(threads) - 4)
    #  (15,2,0) (31,12,0)    (15,2,0) (31,31,0)    20 0x0000000000b41a28 matrixMul.cu    47
    splited = threads[element].replace("\n", "").split()

    # randomly chosen first block and thread
    block = re.match(".*\((\d+),(\d+),(\d+)\).*", splited[0])
    thread = re.match(".*\((\d+),(\d+),(\d+)\).*", splited[1])

    try:
        block_x = block.group(1)
        block_y = block.group(2)
        block_z = block.group(3)

        thread_x = thread.group(1)
        thread_y = thread.group(2)
        thread_z = thread.group(3)
    except:
        raise ValueError

    return [block_x, block_y, block_z], [thread_x, thread_y, thread_z]



"""
Function to run one execution of the fault injector
"""


def run_gdb_fault_injection(section, conf, unique_id):

    ######################## Profiler ########################
    pf = profiler.



    ######################## Injector ########################

    logging = cf.Logging(conf)

    logging.info("Starting GDB script")
    init = conf.getfloat(section, "initSignal")
    end = conf.getfloat(section, "endSignal")
    seqSignals = conf.getint(section, "seqSignals")
    logging.info("initSignal:" + str(init))
    logging.info("endSignal:" + str(end))
    logging.info("seqSignal:" + str(seqSignals))
    timestampStart = int(time.time())



    # Generate configuration file for specific test
    gen_conf_file(conf.get(section, "gdbInitStrings"), conf.get(section, "debug"), unique_id,
                  valid_block, valid_thread, bits_to_flip, fault_model,
                  injection_site)

    # Generate python script for GDB
    gen_flip_script(section)

    # Run pre execution function
    pre_execution(section)

    # Create one thread to start gdb script
    th = RunGDB(section, conf, unique_id)
    # Create numThreadsFI threads to signal app at a random time
    numThreadsFI = conf.getint(section, "numThreadsFI")
    sigThs = list()
    # for i in range(0, numThreadsFI):
    #     sigThs.append(signal_app(section))
    # Start threads
    th.start()
    for sig in sigThs:
        sig.start()

    # Check if app stops execution (otherwise kill it after a time)
    isHang = finish(section)

    # Run pos execution function
    pos_execution(section)

    # Check output files for SDCs
    isSDC = check_sdcs(section)

    # Copy output files to a folder
    save_output(section, isSDC, isHang)

    # Make sure threads finish before trying to execute again
    th.join()
    for sig in sigThs:
        sig.join()
    del sigThs[:]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf', dest="configFile", help='Configuration file', required=True)
    parser.add_argument('-i', '--iter', dest="iterations",
                        help='How many times to repeat the programs in the configuration file', required=True, type=int)




    #
    unique_id = str(uuid.uuid4())
    gdb_fi_log_file = "/tmp/carolfi-" + unique_id + ".log"

    args = parser.parse_args()
    if args.iterations < 1:
        parser.error('Iterations must be greater than zero')

    # Start with a different seed every time to vary the random numbers generated
    # the seed will be the current number of second since 01/01/70
    random.seed()

    # Read the configuration file with data for all the apps that will be executed
    conf = cf.load_config_file(args.configFile)

    num_rounds = 0
    while num_rounds < args.iterations:
        # Execute the fault injector for each one of the sections(apps) of the configuration file
        for sec in conf.sections():
            # Execute one fault injection for a specific app
            run_gdb_fault_injection(sec)
        num_rounds += 1
    os.system("rm -f /tmp/*" + unique_id + "*")


######################## Main ########################

if __name__ == "__main__":
    main()