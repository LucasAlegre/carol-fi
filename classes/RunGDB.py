from multiprocessing import Process
from os import system
import common_functions as cf  # All common functions will be at common_functions module
import common_parameters as cp  # All common parameters will be at common_parameters module

"""
Class RunGdb: necessary to run gdb while
the main thread register the time
If RunGdb execution time > max timeout allowed
this thread will be killed
"""


class RunGDB(Process):
    def __init__(self, unique_id, gdb_exec_name, flip_script, current_dir):
        super(RunGDB, self).__init__()
        self.__gdb_exe_name = gdb_exec_name
        self.__flip_script = flip_script
        self.__unique_id = unique_id
        self.__current_dir = current_dir

    def run(self):
        system("stty tostop")

        if cp.DEBUG:
            print("GDB Thread run, section and id: ", self.__unique_id)

        start_cmd = cf.run_gdb_python(gdb_name=self.__gdb_exe_name, script=self.__flip_script)
        try:
            system(start_cmd + " >" + cp.INJ_OUTPUT_PATH + " 2>" + cp.INJ_ERR_PATH)
        except Exception as err:
            with open(cp.INJ_ERR_PATH, 'w') as file_err:
                file_err.write(str(err))
