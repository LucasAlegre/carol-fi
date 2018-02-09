#!/usr/bin/python
# coding=utf-8
from __future__ import print_function
import os
import time
import datetime
import random
import subprocess
import threading
import re
import filecmp
import shutil
import argparse
import csv
import common_functions as cf

# Debug env var
DEBUG = True

# Injection mode
# 0 -> Instruction output
injection_mode = 0

"""
Class RunGdb: necessary to run gdb while
the main thread register the time
If RunGdb execution time > max timeout allowed
this thread will be killed
"""


class RunGDB(threading.Thread):
    def __init__(self, unique_id, gdb_exec_name, flip_script):
        threading.Thread.__init__(self)
        self.__gdb_exe_name = gdb_exec_name
        self.__flip_script = flip_script
        self.__unique_id = unique_id

    def run(self):
        if DEBUG:
            print("GDB Thread run, section and id: ", self.__unique_id)
        start_cmd = "env CUDA_​DEVICE_​WAITS_​ON_​EXCEPTION=1 " + self.__gdb_exe_name
        start_cmd += " -n -q -batch -x " + self.__flip_script
        os.system(start_cmd)


"""
Signal the app to stop so GDB can execute the script to flip a value
"""


class SignalApp(threading.Thread):
    def __init__(self, signal_cmd, max_wait_time, init, end, seq_signals, logging):
        threading.Thread.__init__(self)
        self.__signal_cmd = signal_cmd
        self.__max_wait_time = max_wait_time
        self.__init = init
        self.__end = end
        self.__seq_signals = seq_signals
        self.__logging = logging

    def run(self):
        # Sleep for a random time
        wait_time = random.uniform(self.__init, self.__end)
        time.sleep(wait_time)
        # Send a series of signal to make sure gdb will flip a value in one of the interrupt signals
        self.__logging.info(
            "sending " + str(self.__seq_signals) + " signals using command: '" + self.__signal_cmd + "' after " + str(
                wait_time) + "s")
        for i in range(0, self.__seq_signals):
            proc = subprocess.Popen(self.__signal_cmd, stdout=subprocess.PIPE, shell=True)
            (out, err) = proc.communicate()
            if out is not None:
                self.__logging.info("shell stdout: " + str(out))
            if err is not None:
                self.__logging.error("shell stderr: " + str(err))
            time.sleep(0.01)


"""
Class SummaryFile: this class will write the information
of each injection in a csv file to make easier data
parsing after fault injection
"""


class SummaryFile:
    # Filename
    __filename = ""
    # csv file
    __csv_file = None
    # Dict reader
    __dict_buff = None
    # Csv Mode
    __mode = None
    # Fieldnames
    __fieldnames = None

    def __init__(self, **kwargs):
        self.__filename = kwargs.get("filename")
        self.__mode = kwargs.get("mode")
        self.__open_file(mode=self.__mode)

        if self.__mode in ['w', 'a']:
            self.__fieldnames = kwargs.get("fieldnames")
            self.__dict_buff = csv.DictWriter(self.__csv_file, self.__fieldnames)
            if self.__mode == 'w':
                self.__dict_buff.writeheader()
        elif self.__mode == 'r':
            self.__dict_buff = csv.DictReader(self.__csv_file)

    """
    Open a file if it exists
    mode can be r or w
    default is r
    """

    def __open_file(self, mode='r'):
        if os.path.isfile(self.__filename) and mode in ['r', 'a']:
            self.__csv_file = open(self.__filename, mode)
        elif mode == 'w':
            self.__csv_file = open(self.__filename, mode)
        else:
            raise IOError(str(self.__filename) + " FILE NOT FOUND")

    """
    To not use __del__ method, close csv file
    """

    def close_csv(self):
        if not self.__csv_file.closed:
            self.__csv_file.close()

    """
    Write a csv row, if __mode == w or a
    row must be a dict
    """

    def write_row(self, row):
        if self.__mode in ['w', 'a']:
            row_ready = {}
            if isinstance(row, list):
                for fields, data in zip(self.__fieldnames, row):
                    row_ready[fields] = data
            else:
                row_ready = row

            self.__dict_buff.writerow(row_ready)

    """
    Read rows, if __mode == r
    return read rows from file in a list
    """

    def read_rows(self):
        if self.__mode == 'r':
            rows = [row for row in self.__dict_buff]
            return rows
        return None


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


def save_output(section, is_sdc, is_hang, conf, logging, unique_id, flip_log_file):
    output_file = conf.get(section, "outputFile")

    # FI successful
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
    if os.path.isfile(output_file) and (not masked) and fi_succ:
        shutil.move(output_file, cp_dir)


"""
Pre execution commands
"""


def pre_execution(conf, section):
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


def pos_execution(conf, section):
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


def check_sdcs(gold_file, output_file, logging):
    if not os.path.isfile(output_file):
        logging.error("outputFile not found: " + str(output_file))
    if os.path.isfile(gold_file) and os.path.isfile(output_file):
        return not filecmp.cmp(gold_file, output_file, shallow=False)
    else:
        return False


"""
Generate environment string for cuda-gdb
valid_block, valid_thread, valid_register, bits_to_flip, fault_model, injection_site, breakpoint_location,
    flip_log_file, debug, gdb_init_strings
The default parameters are necessary for break and signal mode differentiations
"""


def gen_env_string(valid_block, valid_thread, valid_register, bits_to_flip, fault_model,
                   injection_site, breakpoint_location, flip_log_file, debug, gdb_init_strings, inj_type='break'):
    # Block and thread
    env_string = ",".join(str(i) for i in valid_block) + "|" + ",".join(str(i) for i in valid_thread)
    env_string += "|" + valid_register + "|" + ",".join(str(i) for i in bits_to_flip)
    env_string += "|" + str(fault_model) + "|" + injection_site + "|" + breakpoint_location
    env_string += "|" + flip_log_file + "|" + str(debug) + "|" + gdb_init_strings + "|" + inj_type

    os.environ['CAROL_FI_INFO'] = env_string


"""
Function to run one execution of the fault injector
return old register value, new register value
"""


def run_gdb_fault_injection(**kwargs):
    valid_block, valid_thread, injection_address, breakpoint_location = list(), list(), '', ''

    # Declare all FI threads
    thread_signal_list = []

    # This are the mandatory parameters
    inj_mode = kwargs.get('inj_mode')
    bits_to_flip = kwargs.get('bits_to_flip')
    fault_model = kwargs.get('fault_model')
    section = kwargs.get('section')
    unique_id = kwargs.get('unique_id')
    valid_register = kwargs.get('valid_register')
    conf = kwargs.get('conf')

    # Logging file
    flip_log_file = "/tmp/carolfi-flipvalue-" + unique_id + ".log"
    logging = cf.Logging(log_file=flip_log_file, debug=conf.get("DEFAULT", "debug"), unique_id=unique_id)
    logging.info("Starting GDB script")

    # Parameters only for break mode
    if inj_mode == 'break':
        valid_block = kwargs.get('valid_block')
        valid_thread = kwargs.get('valid_thread')
        injection_address = kwargs.get('injection_address')
        breakpoint_location = kwargs.get('breakpoint_location')

    elif inj_mode == 'signal':
        init_signal = float(conf.get("DEFAULT", "initSignal"))
        end_signal = float(conf.get("DEFAULT", "endSignal"))
        signal_cmd = conf.get("DEFAULT", "signalCmd")
        max_wait_time = int(conf.get("DEFAULT", "maxWaitTime"))
        seq_signals = int(conf.get("DEFAULT", "seqSignals"))
        max_num_fi = int(conf.get("DEFAULT", "numThreadsFI"))
        thread_signal_list = [SignalApp(signal_cmd=signal_cmd, max_wait_time=max_wait_time,
                                        init=init_signal, end=end_signal, seq_signals=seq_signals,
                                        logging=logging)] * max_num_fi

    # Generate configuration file for specific test
    gen_env_string(gdb_init_strings=conf.get(section, "gdbInitStrings"),
                   debug=conf.get(section, "debug"),
                   valid_block=valid_block,
                   valid_thread=valid_thread,
                   valid_register=valid_register,
                   bits_to_flip=bits_to_flip,
                   fault_model=fault_model,
                   injection_site=injection_address,
                   breakpoint_location=breakpoint_location,
                   flip_log_file=flip_log_file)

    # Run pre execution function
    pre_execution(conf=conf, section=section)

    # Create one thread to start gdb script
    th = RunGDB(section, conf, unique_id)

    # Start counting time
    timestamp_start = int(time.time())

    # Start fault injection tread
    th.start()

    # Start signal fault injection threads, if this mode was selected
    for t in thread_signal_list:
        t.start()

    # Check if app stops execution (otherwise kill it after a time)
    is_hang = finish(section=section, conf=conf, logging=logging, timestamp_start=timestamp_start)

    # Run pos execution function
    pos_execution(conf=conf, section=section)

    # Check output files for SDCs
    gold_file = conf.get(section, "goldFile")
    output_file = conf.get(section, "outputFile")
    is_sdc = check_sdcs(gold_file=gold_file, output_file=output_file, logging=logging)

    # Make sure threads finish before trying to execute again
    th.join()

    # Also signal ones
    for t in thread_signal_list:
        t.join()

    # Search for set values for register
    # Must be done before save output

    # Was fault injected
    try:
        reg_old_value = logging.search("reg_old_value")
        reg_new_value = logging.search("reg_new_value")
        reg_old_value = re.findall("reg_old_value: (\S+)", reg_old_value)[0]
        reg_new_value = re.findall('reg_new_value: (\S+)', reg_new_value)[0]
        fault_successful = True
    except:
        reg_new_value = reg_old_value = ''
        fault_successful = False

    # Copy output files to a folder
    save_output(
        section=section, is_sdc=is_sdc, is_hang=is_hang, conf=conf, logging=logging, unique_id=unique_id,
        flip_log_file=flip_log_file)  # , gdb_fi_log_file=gdb_fi_log_file)

    return reg_old_value, reg_new_value, fault_successful


"""
Support function to parse a line of disassembled code
"""


def parse_line(instruction_line):
    registers = []
    instruction = ''
    address = ''
    byte_location = ''

    comma_line_count = instruction_line.count(',')

    # INSTRUCTION R1, R2...
    # 0x0000000000b418e8 <+40>: MOV R4, R2
    expression = ".*([0-9a-fA-F][xX][0-9a-fA-F]+) (\S+):[ \t\r\f\v]*(\S+)[ ]*(\S+)" + str(
        ",[ ]*(\S+)" * comma_line_count)

    m = re.match(expression + ".*", instruction_line)
    if m:
        address = m.group(1)
        byte_location = m.group(2)
        instruction = m.group(3)

        # Check register also
        registers = [m.group(4 + i) for i in range(0, comma_line_count + 1)]
        is_valid_line = False
        for r in registers:
            if 'R' in r:
                is_valid_line = True
                break

        if not is_valid_line:
            return None, None, None, None, None
    return registers, address, byte_location, instruction, m


"""
Select a valid stop address
from the file created in the profiler
step
"""


def get_valid_address(addresses):
    m = registers = instruction = address = byte_location = None

    # search for a valid instruction
    while not m:
        element = random.randrange(2, len(addresses) - 1)
        instruction_line = addresses[element]

        registers, address, byte_location, instruction, m = parse_line(instruction_line)

        if DEBUG:
            if not m:
                print("it is stopped here:", instruction_line)
            else:
                print("it choose something:", instruction_line)

    return registers, instruction, address, byte_location


"""
Selects a valid thread for a specific
kernel
return the coordinates for the block
and the thread
"""


def get_valid_thread(threads):
    element = random.randrange(2, len(threads) - 4)
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
Randomly selects a thread, address and a bit location
to inject a fault.
"""


def gen_injection_site(kernel_info_dict):
    global injection_mode
    # A valid block is a [block_x, block_y, block_z] coordinate
    # A valid thread is a [thread_x, thread_y, thread_z] coordinate
    valid_block, valid_thread = get_valid_thread(kernel_info_dict["threads"])

    # A injection site is a list of [registers, instruction, address, byte_location]
    registers, _, injection_site, _ = get_valid_address(kernel_info_dict["addresses"])

    # Randomly select (a) bit(s) to flip
    # Max double bit flip
    bits_to_flip = [0] * 2
    bits_to_flip[0] = random.randint(0, cf.MAX_SIZE_REGISTER - 1)

    # Selects it it is in the instruction output
    # or register file
    valid_register = None
    if injection_mode == 0:
        for i in reversed(registers):
            if 'R' in i:
                valid_register = i
                break

        # Avoid cases like this: MOV R3, 0x2
        if valid_register is None:
            raise ValueError("LINE COULD NOT BE PARSED")

    # Register file
    elif injection_mode == 1:
        raise NotImplementedError

    # Make sure that the same bit is not going to be selected
    r = range(0, bits_to_flip[0]) + range(bits_to_flip[0] + 1, cf.MAX_SIZE_REGISTER)
    bits_to_flip[1] = random.choice(r)

    return valid_thread, valid_block, valid_register, bits_to_flip, injection_site


"""
This injector has two injection options
this function performs fault injection
by sending a OS signal to the application
"""


def fault_injection_by_signal(conf, fault_models, inj_type, iterations, summary_file):
    for num_rounds in range(iterations):
        # Execute the fault injector for each one of the sections(apps) of the configuration file
        for fault_model in fault_models:
            unique_id = str(num_rounds) + "_" + str(inj_type) + "_" + str(fault_model)
            r_old_val, r_new_val, fault_succ = run_gdb_fault_injection(unique_id=unique_id, inj_mode='signal',
                                                                       fault_model=fault_model, section="DEFAULT",
                                                                       valid_register="R30", conf=conf)
            # Write a row to summary file
            row = [unique_id, num_rounds, fault_model]
            row.extend([None, None, None])
            row.extend([None, None, None])
            row.extend(
                [r_old_val, r_new_val, 0, "", "", "", fault_succ])
            summary_file.write_row(row=row)


"""
This injector has two injection options
this function performs fault injection
by creating a breakpoint and steping into it
"""


def fault_injection_by_breakpointing(conf, fault_models, inj_type, iterations, kernel_info_list, summary_file):
    for num_rounds in range(iterations):
        # Execute the fault injector for each one of the sections(apps) of the configuration file
        for fault_model in fault_models:
            # Execute one fault injection for a specific app
            # For each kernel
            for kernel_info_dict in kernel_info_list:
                # Generate an unique id for this fault injection
                unique_id = str(num_rounds) + "_" + str(inj_type) + "_" + str(fault_model)
                try:
                    valid_thread, valid_block, valid_register, bits_to_flip, injection_address = gen_injection_site(
                        kernel_info_dict=kernel_info_dict)
                    print("Injection:", num_rounds, "fault model:", fault_model, "kernel:",
                          kernel_info_dict["kernel_name"])
                    breakpoint_location = str(kernel_info_dict["kernel_name"] + ":"
                                              + kernel_info_dict["kernel_line"])
                    r_old_val, r_new_val, fault_succ = run_gdb_fault_injection(section="DEFAULT", conf=conf,
                                                                               unique_id=unique_id,
                                                                               valid_block=valid_block,
                                                                               valid_thread=valid_thread,
                                                                               valid_register=valid_register,
                                                                               bits_to_flip=bits_to_flip,
                                                                               injection_address=injection_address,
                                                                               fault_model=fault_model,
                                                                               breakpoint_location=breakpoint_location)
                    # Write a row to summary file
                    row = [unique_id, num_rounds, fault_model]
                    row.extend(valid_thread)
                    row.extend(valid_block)
                    row.extend(
                        [r_old_val, r_new_val, 0, injection_address, valid_register, breakpoint_location, fault_succ])
                    summary_file.write_row(row=row)
                except Exception as err:
                    print("\nFault was not injected\n", str(err))
                    num_rounds -= 1
                time.sleep(2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf', dest="config_file", help='Configuration file', required=True)
    parser.add_argument('-i', '--iter', dest="iterations",
                        help='How many times to repeat the programs in the configuration file', required=True, type=int)
    parser.add_argument('-l', '--log_csv', dest="csv_file", help="CSV log file", type=str, required=False)
    parser.add_argument('-t', '--inj_type', dest="inj_type",
                        help="The CAROL-FI cuda could inject faults in two ways, by using a breakpoint or a thread signal",
                        required=False, default='break')

    args = parser.parse_args()
    if args.iterations < 1:
        parser.error('Iterations must be greater than zero')

    # Start with a different seed every time to vary the random numbers generated
    # the seed will be the current number of second since 01/01/70
    random.seed()

    # Read the configuration file with data for all the apps that will be executed
    conf = cf.load_config_file(args.config_file)

    # First set env vars
    os.environ['PYTHONPATH'] = "$PYTHONPATH:" + os.path.dirname(os.path.realpath(__file__))
    os.environ['CAROL_FI_INFO'] = conf.get("DEFAULT", "gdbInitStrings") + "|" + conf.get("DEFAULT",
                                                                                         "kernelBreaks")
    ########################################################################
    # Profiler step
    profiler_cmd = conf.get("DEFAULT", "gdbExecName") + " -n -q -batch -x profiler.py"
    os.system(profiler_cmd)
    ########################################################################
    # Injector setup

    # Load information file generated in profiler step
    kernel_info_list = cf.load_file(cf.KERNEL_INFO_DIR)

    # Get fault models
    fault_models = range(0, int(conf.get('DEFAULT', 'faultModel')) + 1)

    # Csv log
    fieldnames = ['unique_id', 'iteration', 'fault_model', 'thread_x', 'thread_y', 'thread_z',
                  'block_x', 'block_y', 'block_z', 'old_value', 'new_value',
                  'injection_address', 'register', 'fault_successful']

    ########################################################################
    # Fault injection
    inj_type = args.inj_type
    iterations = args.iterations

    # Creating a summary csv file
    summary_file = SummaryFile(filename=args.csv_file, fieldnames=fieldnames, mode='w')

    # break mode is default option
    if inj_type == 'break':
        fault_injection_by_breakpointing(conf=conf, fault_models=fault_models, inj_type=inj_type, iterations=iterations,
                                         kernel_info_list=kernel_info_list, summary_file=summary_file)
    elif inj_type == 'signal':
        # The hard mode
        fault_injection_by_signal(conf=conf, fault_models=fault_models, inj_type=inj_type, iterations=iterations,
                                  summary_file=summary_file)

    # Clear /tmp files generated
    os.system("rm -f /tmp/carol-fi-kernel-info.txt")
    summary_file.close_csv()
    ########################################################################


########################################################################
#                                   Main                               #
########################################################################

if __name__ == "__main__":
    main()

"""
LEGACY
"""

# """
# Generate config file for the gdb flip_value script
# """
#
#
# def gen_conf_file(gdb_init_strings, debug, unique_id, valid_block,
#                   valid_thread, valid_register, bits_to_flip, fault_model,
#                   injection_site, breakpoint_location, flip_log_file):
#     if sys.version_info >= (3, 0):
#         f_conf = configparser.SafeConfigParser()
#     else:
#         f_conf = ConfigParser.SafeConfigParser()
#
#     f_conf.set("DEFAULT", "flipLogFile", flip_log_file)
#     f_conf.set("DEFAULT", "debug", debug)
#     f_conf.set("DEFAULT", "gdbInitStrings", gdb_init_strings)
#     f_conf.set("DEFAULT", "faultModel", str(fault_model))
#     f_conf.set("DEFAULT", "injectionSite", injection_site)
#     f_conf.set("DEFAULT", "validThread", ";".join(valid_thread))
#     f_conf.set("DEFAULT", "validBlock", ";".join(valid_block))
#     f_conf.set("DEFAULT", "validRegister", valid_register)
#     f_conf.set("DEFAULT", "bitsToFlip", ";".join(str(i) for i in bits_to_flip))
#     f_conf.set("DEFAULT", "breakpointLocation", breakpoint_location)
#
#     fp = open("/tmp/flip-" + unique_id + ".conf", "w")
#     f_conf.write(fp)
#     fp.close()


# """
# Generate the gdb profiler script
# """
#
#
# def gen_profiler_script(unique_id, conf_filename):
#     fp = open("profiler.py", "r")
#     p_script = fp.read()
#     fp.close()
#     profiler_filename = "/tmp/profiler-" + unique_id + ".py"
#     fp = open(profiler_filename, "w")
#
#     fp.write(p_script.replace("<conf-location>", conf_filename))
#     fp.close()
#     os.chmod(profiler_filename, 0o775)
#     return profiler_filename
#
# """
# Generate the gdb flip_value script
# """
#
#
# def gen_flip_script(unique_id):
#     fp = open("flip_value.py", "r")
#     p_script = fp.read()
#     fp.close()
#     fp = open("/tmp/flip-" + unique_id + ".py", "w")
#
#     p_script = p_script.replace("<conf-location>", "/tmp/flip-" + unique_id + ".conf")
#     p_script = p_script.replace("<home-location>", "/home/carol/carol-fi")
#     fp.write(p_script)
#     fp.close()
#     os.chmod("/tmp/flip-" + unique_id + ".py", 0o775)
