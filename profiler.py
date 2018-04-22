import gdb
import os
import common_functions as cf  # All common functions will be at common_functions module

import common_parameters as cp # All commom parameters

# This list will contains all kernel info
kernel_info_list = []

"""
Get kernel Threads and addresses information
necessary to fault injection
"""


def get_kernel_address_event(event):
    global kernel_info_list, global_check_kludge
    if global_check_kludge:
        return

    # Search all kernels info, and all breakpoints
    for kernel_info in kernel_info_list:
        for breakpoint in event.breakpoints:
            # Get the addresses and thread for this kernel
                # Thread info
                kernel_info["threads"] = cf.execute_command(gdb, "info cuda threads")
                kernel_info["addresses"] = cf.execute_command(gdb, "disassemble")

                # gdb.flush()
                breakpoint.delete()
                kernel_info["breakpoint"] = None
                # Need to continue after get the kernel information
                gdb.execute("c")


"""
Set temporary breakpoints.
After they are hit they are deleted
"""


class ProfilerBreakpoint(gdb.Breakpoint):

    def __init__(self, *args, **kwargs):
        try:
            self.__kludge = kwargs.pop('kludge')
        except:
            self.__kludge = False

        self.__kernel_line = kwargs.get('spec')
        super(ProfilerBreakpoint, self).__init__(*args, **kwargs)

    def get_kernel_line(self):
        return self.__kernel_line

    def stop(self):
        if self.__kludge:
            return True

        for kernel_info in kernel_info_list:
            if kernel_info["breakpoint"].get_kernel_line() == self.__kernel_line:
                kernel_info["threads"] = cf.execute_command(gdb, "info cuda threads")
                kernel_info["addresses"] = cf.execute_command(gdb, "disassemble")
        return True


def set_breakpoints(kernel_conf_string):
    # We are going to set
    # temporary breakpoints
    # to retrieve info of each
    # kernel
    global kernel_info_list
    breakpoints_list = kernel_conf_string.split(";")
    for kernel_line in breakpoints_list:
        # Just to make sure things like this: kernel.cu:52;<nothing here>
        if len(kernel_line) > 0:
            kernel_places = kernel_line.split("-")
            k_l = kernel_places[0]
            kernel_info = {
                'breakpoint': ProfilerBreakpoint(spec=str(k_l), type=gdb.BP_BREAKPOINT, temporary=True),
                'kernel_name': kernel_places[0].split(":")[0],
                'kernel_line': kernel_places[0].split(":")[1],
                'kernel_end_line': kernel_places[1].split(":")[1]
            }
            kernel_info_list.append(kernel_info)


"""
Main function
"""


def main():
    global kernel_info_list, global_check_kludge

    # Initialize GDB to run the app
    gdb.execute("set confirm off")
    # gdb.execute("set pagination off")
    gdb_init_strings, kernel_conf_string, time_profiler, kludge = str(os.environ["CAROL_FI_INFO"]).split("|")
    # print(gdb_init_strings)

    try:

        for init_str in gdb_init_strings.split(";"):
            gdb.execute(init_str)

    except gdb.error as err:
        print ("initializing setup: " + str(err))


    # Profiler has two steps
    # First: getting kernel information
    # Run app for the first time
    kludge_breakpoint = None
    if time_profiler == 'False':
        if kludge != 'None':
            kludge_breakpoint = ProfilerBreakpoint(spec=kludge, type=gdb.BP_BREAKPOINT, temporary=True, kludge=True)
            global_check_kludge = True

        set_breakpoints(kernel_conf_string)
        # gdb.events.stop.connect(get_kernel_address_event)

    gdb.execute("r")

    if kludge_breakpoint:
        # kludge_breakpoint.delete()
        del kludge_breakpoint
        global_check_kludge = False
        gdb.execute("c")

    # Second: save the retrieved information on a txt file
    # Save the information on file to the output
    if time_profiler == 'False':
        for kernel_info in kernel_info_list:
            # kernel_info["breakpoint"].delete()
            del kernel_info["breakpoint"]
            kernel_info["breakpoint"] = None
        cf.save_file(cp.KERNEL_INFO_DIR, kernel_info_list)

# Global kludge var
global_check_kludge = None

main()
