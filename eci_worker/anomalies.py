import subprocess
import os, sys
import multiprocessing
import time
import shutil
from rq import get_current_job


def example(seconds):
    job = get_current_job()
    print('Starting task')
    for i in range(seconds):
        job.meta['progress'] = 100.0 * i / seconds
        job.save_meta()
        print(i)
        time.sleep(1)
    job.meta['progress'] = 100
    job.save_meta()
    print('Task completed')


def dummy(stime=10):
    '''
    Dummy anomaly to gauge detection bias
    :param stime: Number of seconds to sleep
    :return:
    '''
    time.sleep(stime)


def sim_work_cpu(cmd):
    FNULL = open(os.devnull, 'w')
    return subprocess.run(cmd, stdout=FNULL, stderr=subprocess.STDOUT)


def sim_work_cpu_p(cmd, time_out=15):
    '''
    Starts a subprocess and runs it for the amount set
    :param cmd: command to run
    :param time_out: seconds to run command
    :return:
    '''
    FNULL = open(os.devnull, 'w')
    p1 = subprocess.Popen(cmd, stdout=FNULL, stderr=subprocess.PIPE)
    try:
        outs, errs = p1.communicate(
            timeout=time_out)  # will raise error and kill any process that runs longer than 60 seconds
    except subprocess.TimeoutExpired as e:
        p1.kill()

        # outs, errs = p1.communicate()
        # print(outs)
        # print(errs)


def cpu_overload(half=True):
    '''
    Detects the number of CPU cores and runs full load on all or half of the CPUS
    :param half: Boolean to run on half the nodes
    :return:
    '''
    cpu_count = multiprocessing.cpu_count()
    if half:
        cpu_count = int(cpu_count/2)
    pool = multiprocessing.Pool(processes=cpu_count)
    try:
        pool.map(sim_work_cpu_p, ["yes", ">", "/dev/null"] * cpu_count)
    except OSError:
        print("OS Error")


def memeater(multiplier=1):
    i = 0
    test = {}
    stop = 0
    gb = 1024*1024*1024
    limit = multiplier*gb
    limit = 1000000  # 133.8
    limit = 100000000  # 844.3
    limit = 10000000000  # 25.43 GB
    limit = 1000000000  # 25.43 GB
    while stop < limit:
        test[i] = i * i
        i = i + 1
        stop += 1
    time.sleep(10)


def memeater_v2(multiplier=1):
    '''
    Eats memory a GB at a time or based on a multiplier
    :param multiplier: Multiplies the number of GB from RAM to allocate
    :return:
    '''
    gb = 1024*1024*1024
    a = "a" * (multiplier * gb)
    time.sleep(10)


def generate_large_file(multiplier=1):
    '''
    Generates a file in MB or GB range
    :param multiplier:
    :return:
    '''
    unit = 1024
    size = pow(unit, multiplier)
    data_dir = '/Users/Gabriel/Documents/workspaces/ede-chaos-inductor/data'
    tmp_file = os.path.join(data_dir, 'large.blob')
    with open(tmp_file, "wb") as f:
        f.write("0".encode() * size)


def copy(remove=True):
    '''
    Copy large file to 3 location
    :return:
    '''
    data_dir = '/Users/Gabriel/Documents/workspaces/ede-chaos-inductor/data'
    mv_dir_1 = '/Users/Gabriel/Documents/workspaces/ede-chaos-inductor/data/mv1'
    mv_dir_2 = '/Users/Gabriel/Documents/workspaces/ede-chaos-inductor/data/mv2'
    file_path = os.path.join(data_dir, 'large.blob')
    if not os.path.isfile(file_path):
        generate_large_file()
    shutil.move(file_path, os.path.join(mv_dir_1, 'large.blob'))
    time.sleep(10)
    shutil.move(os.path.join(mv_dir_1, 'large.blob'), os.path.join(mv_dir_2, 'large.blob'))
    time.sleep(10)
    shutil.move(os.path.join(mv_dir_2, 'large.blob'), file_path)
    time.sleep(10)
    if remove:
        os.remove(file_path)



if __name__ == '__main__':
    # cpu_overload(True)
    # memeater()
    # memeater_v2(3)
    # generate_large_file()
    copy()