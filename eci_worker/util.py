import yaml
import os
import sys


def load_yaml(file):
    etc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc'))
    file_path = os.path.join(etc_path, file)
    if not os.path.isfile(file_path):
        print("File not found at location {}".format(file_path))
        sys.exit(1)
    with open(file_path) as cfile:
        config = yaml.load(cfile, Loader=yaml.FullLoader)
    return config

# print(load_yaml('cpu_overload.yaml')['time_out'])


def save_yaml(file, data):
    etc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc'))
    file_path = os.path.join(etc_path, file)
    with open(file_path, 'w+') as cfile:
        yaml.dump(data, cfile, allow_unicode=True)


def parse_logs(log_file):
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
    file_path = os.path.join(log_dir, log_file)
    with open(file_path) as fp:
        for line in fp:
            ut = line.split(' ')[0]
            message = line.split('INFO')[-1].lstrip()
            uuid = line.split('INFO')[-1].lstrip().split(' ')[-1]
            status = line.split('INFO')[-1].lstrip().split(' ')[0]
            ano_type = line.split('INFO')[-1].lstrip().split(' ')[1]
            settings = line.split('INFO')[-1].lstrip().split('with')[1].split('and')[0].lstrip().rstrip()
            print(ut)
            print(message)
            print(uuid)
            print(status)
            print(ano_type)
            print(settings)
            print(line.split('INFO')[-1].lstrip().split('with')[1].split('and')[0])
            # print("Line {}: {}".format(cnt, line))

# parse_logs('dummy-out.log')
parse_logs('cpu_overload-out.log')