import gdb
import sys
import re

########################################################################
# Global vars
# Unfortunately gdb cannot see common_functions.py
home_dir = "<home-location>"
sys.path.append(home_dir)
import common_functions as cf  # All common functions will be at common_functions module

# global vars loaded from config file
conf_location = "<conf-location>"

"""
function called when the execution is stopped
"""


def fault_injection(event):
    global global_valid_block, global_valid_thread, global_valid_register
    global global_bits_to_flip, global_fault_model, global_fi, global_logging

    # Ensure fault was injected
    fi_succ = False

    # This if avoid the creation of another event connection
    # for some reason gdb cannot breakpoint addresses before
    # a normal breakpoint is hit
    if global_fi:

        global_logging.debug("Trying Fault Injection")

        try:
            change_focus_cmd = "cuda kernel 0 block {0},{1},{2} thread {3},{4},{5}".format(str(global_valid_block[0]),
                                                                                           str(global_valid_block[1]),
                                                                                           str(global_valid_block[2]),
                                                                                           str(global_valid_thread[0]),
                                                                                           str(global_valid_thread[1]),
                                                                                           str(global_valid_thread[2]))
            thread_focus = gdb.execute(change_focus_cmd, to_string=True)

            # Thread focus return information
            global_logging.info(str(thread_focus).replace("[", "").replace("]", "").strip())

            # Do the fault injection magic
            fi_succ = generic_injector(global_valid_register, global_bits_to_flip, global_fault_model)

        except Exception as err:
            global_logging.exception("fault_injection_python_exception: " + str(err))
    else:
        global_fi = True

    if fi_succ:
        global_logging.exception("Fault Injection Successful")
    else:
        global_logging.exception("Fault Injection Went Wrong")


"""
Flip only a bit in a register content
"""


def flip_a_bit(bit_to_flip, reg_content):
    new_bit = '0' if reg_content[bit_to_flip] == '1' else '1'
    reg_content = reg_content[:bit_to_flip] + new_bit + reg_content[bit_to_flip + 1:]
    return reg_content


"""
Flip a bit or multiple bits based on a fault model
"""


def generic_injector(valid_register, bits_to_flip, fault_model):
    # get register content
    reg_cmd = cf.execute_command(gdb, "p/t $" + str(valid_register))

    m = re.match('\$(\d+)[ ]*=[ ]*(\S+).*', reg_cmd[0])

    if m:
        reg_content = str(m.group(2))
        # Make sure that binary value will have max size register
        reg_content_old = str('0' * (cf.MAX_SIZE_REGISTER - len(reg_content))) + reg_content
        # Logging info result extracted from register
        global_logging.info("reg old value: " + reg_content_old)
        reg_content_new = ''

        # Single bit flip
        if fault_model == 0:
            # single bit flip
            reg_content_new = flip_a_bit(bits_to_flip[0], reg_content_old)

        # Double bit flip
        elif fault_model == 1:
            # multiple bit flip
            for bit_to_flip in bits_to_flip:
                reg_content_new = flip_a_bit(bit_to_flip, reg_content_old)

        # Random value
        elif fault_model == 2:
            # random value is stored at bits_to_flip[0]
            reg_content_new = str(bits_to_flip[0])

        # Zero values
        elif fault_model == 3:
            reg_content_new = '0'

        # Least significant bits, not implemented
        elif fault_model == 4:
            raise NotImplementedError

        reg_content_fliped = str(int(reg_content_new, 2))
        # send the new value to gdb
        reg_cmd_flipped = cf.execute_command(gdb, "set $" + str(valid_register) + " = " + reg_content_fliped)

        global_logging.info("reg new value: " + str(reg_content_new))

        # Log command return only something was printed
        if len(reg_cmd_flipped) > 0:
            global_logging.info("flip command return: " + str(reg_cmd_flipped))

        # Return the fault confirmation
        return reg_content_old != reg_content_new
    else:
        raise NotImplementedError


"""
Handler attached to exit event
"""


def exit_handler(event):
    global_logging.info(str("event type: exit"))
    try:
        global_logging.info(str("exit code: %d" % event.exit_code))
    except:
        global_logging.exception(str("exit code: no exit code available"))


"""
Handler attached to crash event
"""


def abnormal_stop(event):
    global_logging.debug("Abnormal stop, signal:" + str(event.stop_signal))


"""
Main function
"""


def main():
    global global_valid_block, global_valid_thread, global_valid_register
    global global_bits_to_flip, global_fault_model, global_logging

    # Initialize GDB to run the app
    gdb.execute("set confirm off")
    gdb.execute("set pagination off")

    # Connecting to a exit handler event
    gdb.events.exited.connect(exit_handler)

    # Setting conf and loading global vars
    conf = cf.load_config_file(conf_location)

    # Get variables values from config file
    global_valid_block = conf.get("DEFAULT", "validBlock").split(";")
    global_valid_thread = conf.get("DEFAULT", "validThread").split(";")
    global_valid_register = conf.get("DEFAULT", "validRegister")
    global_bits_to_flip = [int(i) for i in conf.get("DEFAULT", "bitsToFlip").split(";")]
    global_fault_model = int(conf.get("DEFAULT", "faultModel"))
    injection_site = conf.get("DEFAULT", "injectionSite")
    breakpoint_location = conf.get("DEFAULT", "breakpointLocation")

    # Logging
    global_logging = cf.Logging(log_file=conf.get("DEFAULT", "flipLogFile"), debug=conf.get("DEFAULT", "debug"))
    global_logging.info("Starting flip_value script")
    try:
        gdb_init_strings = conf.get("DEFAULT", "gdbInitStrings")

        for init_str in gdb_init_strings.split(";"):
            gdb.execute(init_str)
            global_logging.info("initializing setup: " + str(init_str))

    except gdb.error as err:
        print("initializing setup: " + str(err))

    # Place the first breakpoint, it is only to avoid
    # address memory error
    breakpoint_kernel_line = gdb.Breakpoint(spec=breakpoint_location, type=gdb.BP_BREAKPOINT)

    # Define which function to call when the execution stops, e.g. when a breakpoint is hit
    # or a interruption signal is received
    gdb.events.stop.connect(fault_injection)

    # Start app execution
    gdb.execute("r")
    breakpoint_kernel_line.delete()
    breakpoint_kernel_address = gdb.Breakpoint(spec="*" + injection_site, type=gdb.BP_BREAKPOINT)

    # Continue execution until the next breakpoint
    gdb.execute("c")
    breakpoint_kernel_address.delete()


# Set global vars
global_valid_block = None
global_valid_thread = None
global_valid_register = None
global_bits_to_flip = None
global_fault_model = None
global_logging = None
global_fi = False

# Call main execution
main()
