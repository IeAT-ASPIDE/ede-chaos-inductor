import yaml
import os
import sys


def load_yaml(file):
    etc_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'etc'))
    file_path = os.path.join(etc_path, file)
    if not os.path.isfile(file_path):
        print("File not found at location {}".format(file_path))
        sys.exit(1)
    with open(file_path) as cfile:
        config = yaml.load(cfile, Loader=yaml.FullLoader)
    return config

