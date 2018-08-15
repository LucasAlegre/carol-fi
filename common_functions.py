import os
import pickle
import sys

if sys.version_info >= (3, 0):
    import configparser  # python 3
else:
    import ConfigParser  # python 2

"""
Support function to execute a command
and return the output.
If the command contains NEWLINE character
it will result in a list.
"""


def execute_command(gdb, to_execute):
    ret = gdb.execute(to_execute, to_string=True)
    return ret.splitlines()


"""
Serialize a dictionary into a
file path using pickle.
"""


def save_file(file_path, data):
    f_out = open(file_path, "wb")
    pickle.dump(data, f_out)
    f_out.close()


"""
Load a dictionary from a file path using pickle.
return a dictionary
"""


def load_file(file_path):
    f_in = open(file_path, "rb")
    data = pickle.load(f_in)
    f_in.close()
    return data


"""
Read configuration file
"""


def load_config_file(flip_config_file):
    # Read configuration file
    if sys.version_info >= (3, 0):
        conf = configparser.ConfigParser()
    else:
        conf = ConfigParser.ConfigParser()

    conf.read(flip_config_file)
    return conf


"""
Kill all remaining processes
"""


def kill_all(conf):
    for cmd in str(conf.get("DEFAULT", "killStrs")).split(";"):
        os.system(cmd)


"""
Run gdb python script with specific parameters
It makes standart gdb script calls
"""


def run_gdb_python(gdb_name, script):
    cmd = 'env CUDA_DEVICE_WAITS_ON_EXCEPTION=1 ' + gdb_name
    cmd += ' -n -batch -x ' + script  # -batch-silent
    # -n --nh --nx -q --return-child-result -x
    return cmd


"""
GDB python cannot find common_functions.py, so I added this directory to PYTHONPATH
"""


def set_python_env():
    current_path = os.path.dirname(os.path.realpath(__file__))
    os.environ['PYTHONPATH'] = "$PYTHONPATH:" + current_path + ":" + current_path + "/classes"
    return current_path
