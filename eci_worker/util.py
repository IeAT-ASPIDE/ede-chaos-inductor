import yaml
import os
import signal
import sys
import glob
from pygrok import Grok


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


def save_pid(pid, file):
    etc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc'))
    pid_loc = os.path.join(etc_path, file)
    with open(pid_loc, 'w') as f:
        f.write(str(pid))


def clean_up_pid(file):
    etc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc'))
    pid_loc = os.path.join(etc_path, file)
    if not os.path.isfile(pid_loc):
        return -1
    os.remove(pid_loc)
    return 0


def kill_pid(pid):
    os.kill(pid, signal.SIGTERM)


def get_pid_from_file(file, check=False):
    etc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc'))
    pid_loc = os.path.join(etc_path, file)
    if not os.path.isfile(pid_loc):
        return -1
    else:
        with open(pid_loc, 'r') as f:
            pid = f.readline()
        if check:
            if check_pid(int(pid)):
                return 1
            else:
                return 0
        return pid


def get_list_workers():
    etc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc'))
    g_dir = "{}/*.pid".format(etc_path)
    list_workers = []
    for name in glob.glob(g_dir):
        list_workers.append(name)
    return list_workers


def check_pid(pid):
    """ Check For the existence of a unix pid. """
    try:
        os.kill(int(pid), 0)
    except OSError:
        return False
    else:
        return True


def load_sx():
    etc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc'))
    xfile = os.path.join(etc_path, 's.x')
    with open(xfile) as f:
        s = f.readline()
    return s


def parse_logs_old(log_file):
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


def parse_logs(file,
               type=None):
    if type == 'copy':
        pattern = '%{NUMBER:unixtime}  anomalies.py:%{NUMBER:linenumber} 	%{LOGLEVEL:loglevel}     %{WORD:status} %{WORD:anomaly_name} with options %{GREEDYDATA:settings} and uuid %{GREEDYDATA:uuid}'
    elif type == 'cpu':
        pattern = '%{NUMBER:unixtime}  anomalies.py:%{NUMBER:linenumber}  	%{LOGLEVEL:loglevel}     %{WORD:status} %{WORD:anomaly_name} with options %{GREEDYDATA:settings} and uuid %{GREEDYDATA:uuid}'
        # pattern = '%{NUMBER:unixtime}  anomalies.py:%{NUMBER:linenumber}%{GREEDYDATA}%{LOGLEVEL:loglevel}     %{WORD:status} %{WORD:anomaly_name} with options %{GREEDYDATA:settiongs} and uuid %{GREEDYDATA:uuid}'
    else:
        pattern = '%{NUMBER:unixtime}  anomalies.py:%{NUMBER:linenumber} 	%{LOGLEVEL:loglevel}     %{WORD:status} %{WORD:anomaly_name} with options %{GREEDYDATA:settings} and uuid %{GREEDYDATA:uuid}'
    grok = setup_grok(pattern)
    with open(file, 'r') as log:
        lines = log.readlines()

    for line in lines:
        match = grok.match(line)
        print(match)


def setup_grok(pattern):
    grok = Grok(pattern)
    return grok

# parse_logs('dummy-out.log')
# parse_logs('cpu_overload-out.log')

# save_pid(13080, 'worker.pid')
#
# print(get_pid_from_file('worker_a84a551ef6524f2d8aac2d187a306eed.pid'))
# print(load_sx())

# print(dir(anomalies))
# print(help(anomalies))


if __name__ == '__main__':
    copy_text =  '1588248878.329905  anomalies.py:194 	INFO     Started copy with options [unit mb, multiplier 4, remove True, time_out 10] and uuid 90a9dd57-ad60-4df7-aa12-43c36ab0c631'
    copy_pattern = '%{NUMBER:unixtime}  anomalies.py:%{NUMBER:linenumber} 	%{LOGLEVEL:loglevel}     %{WORD:status} %{WORD:anomaly_name} with options %{GREEDYDATA:settiongs} and uuid %{GREEDYDATA:uuid}'
    copy_file = '/Users/Gabriel/Documents/workspaces/ede-chaos-inductor/logs/copy-out.log'
    # parse_logs(copy_file, 'copy')

    text2 = '1588251588.749776  anomalies.py:83  	INFO     Started CPU_overload with options [half True, time_out 15]  and uuid 0377d8ed-3221-4fe8-9bea-502f369b0fb3'
    cpu_pattern = '%{NUMBER:unixtime}  anomalies.py:%{NUMBER:linenumber}  	%{LOGLEVEL:loglevel}     %{WORD:status} %{WORD:anomaly_name} with options %{GREEDYDATA:settiongs} and uuid %{GREEDYDATA:uuid}'
    cpu_file = '/Users/Gabriel/Documents/workspaces/ede-chaos-inductor/logs/cpu_overload-out.log'
    # parse_logs(cpu_file, 'cpu')

    ddot_file = '/Users/Gabriel/Documents/workspaces/ede-chaos-inductor/logs/ddot-out.log'
    # parse_logs(ddot_file)

    dummy_file = '/Users/Gabriel/Documents/workspaces/ede-chaos-inductor/logs/dummy-out.log'
    parse_logs(dummy_file)