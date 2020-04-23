import subprocess
import os, sys
import multiprocessing
import time
import shutil
from rq import get_current_job
import cpuinfo
import numpy as np
from sys import getsizeof
import random
from eci_worker.anomaly_loggers import setup_logger
import uuid

log_dummy = setup_logger('dummy')
log_cpu = setup_logger('cpu_overload')
log_memv2 = setup_logger('mem_eater')
log_copy = setup_logger('copy')
log_ddot = setup_logger('ddot')

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
    uid = uuid.uuid4()
    log_dummy.info("Started dummy with stime {} and uuid {}".format(stime, uid))
    time.sleep(stime)
    log_dummy.info("Finished dummy with stime {} and uuid {}".format(stime, uid))


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
            timeout=time_out)  # will raise error and kill any process that runs longer than set by time_out
    except subprocess.TimeoutExpired as e:
        p1.kill()
        # outs, errs = p1.communicate()
        # print(outs)
        # print(errs)


def cpu_overload(settings):
    '''
    Detects the number of CPU cores and runs full load on all or half of the CPUS
    :param half: Boolean to run on half the nodes
    :return:
    '''
    uid = uuid.uuid4()
    log_cpu.info("Started CPU overload with settings {} and uuid {}".format(settings, uid))
    half = settings['half']
    cpu_count = multiprocessing.cpu_count()
    if half:
        cpu_count = int(cpu_count/2)
    pool = multiprocessing.Pool(processes=cpu_count)
    try:
        pool.map(sim_work_cpu_p, ["yes", ">", "/dev/null"] * cpu_count)
    except OSError:
        print("OS Error")
    log_cpu.info("Finished CPU overload with settings {} and uuid {}".format(settings, uid))


def memeater_v1(unit='mb', multiplier=1, time_out=10):
    '''
    Loop that allocates memory in chuncks of MB or GB.
    :param unit: MB or GB to allocate
    :param multiplier: how much of each unit to set
    :param time_out: Seconds to wait until exiting
    Resulting limit approx. value
    limit = 1000000  # 133.8 MB
    limit = 100000000  # 844.3 MB
    limit = 10000000000  # 25.43 GB
    limit = 1000000000  # 25.43 GB
    :return:
    '''
    i = 0
    test = {}
    stop = 0
    if unit == 'mb':
        n_unit = pow(1024, 2)
    elif unit == 'gb':
        n_unit = pow(1024, 3)
    else:
        n_unit = pow(1024, 2)
    limit = multiplier*n_unit
    while stop < limit:
        test[i] = i * i
        i = i + 1
        stop += 1
    time.sleep(time_out)


def memeater_v2(unit='gb', multiplier=1, iteration=2, time_out=20):
    '''
    Eats memory a GB at a time or based on a multiplier.
    If iteration is set to high number than it can simulates a memory leak
    :param unit: MB or GB to allocate
    :param multiplier: Multiplies the number of units from RAM to allocate
    :param iteration: How many iterations to perform and memory to allocate
    :param time_out: Seconds to wait until exiting
    '''
    uid = uuid.uuid4()

    if unit == 'kb':
        n_unit = 1024
    elif unit == 'mb':
        n_unit = pow(1024, 2)
    elif unit == 'gb':
        n_unit = pow(1024, 3)
    else:
        n_unit = pow(1024, 2)
    log_memv2.info("Starting Memeaterv2 with unit {}, multiplier {}, iteration {}, time_out {} and uuid {}".format(
        unit, multiplier, iteration, time_out, uid))
    b = []
    for it in range(0, iteration):
        a = "a" * (multiplier * n_unit)
        b.append(a)
        time.sleep(time_out)
    log_memv2.info("Finised Memeaterv2 with unit {}, multiplier {}, iteration {}, time_out {} and uuid {}".format(
        unit, multiplier, iteration, time_out, uid))


def generate_large_file(unit='mb', multiplier=1):
    '''
    Generates a file in MB or GB range
    :param unit: MB or GB to allocate
    :param multiplier: Multiplies the number of units from RAM to allocate
    :return:
    '''
    if unit == 'kb':
        n_unit = 1024
    elif unit == 'mb':
        n_unit = pow(1024, 2)
    elif unit == 'gb':
        n_unit = pow(1024, 3)
    else:
        n_unit = 1024
    size = n_unit * multiplier
    log_copy.info('Generating file of size {} with {} and {}'.format(size, multiplier, unit))
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    tmp_file = os.path.join(data_dir, 'large.blob')
    with open(tmp_file, "wb") as f:
        f.write("0".encode() * size)
    log_copy.info('Finished generating file of size {} with {} and {}'.format(size, multiplier, unit))


def copy(unit='kb', multiplier=1, remove=True, time_out=10):
    '''
    Copy large file to 3 location, simulating HDD decgradation and interference
    :param unit: KB, MB or GB to allocate
    :param multiplier: Multiplies the number of units for the given file
    :param remove: Deletes file when done
    :param time_out: Seconds to wait until mv operation
    :return:
    '''
    uid = uuid.uuid4()
    log_copy.info("Started copy with unti {}, multiplier {}, remove {}, time_out {} and uuid {}".format(
        unit, multiplier, remove, time_out, uid))
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    mv_dir_1 = os.path.join(data_dir, 'mv1')
    mv_dir_2 = os.path.join(data_dir, 'mv2')
    if not os.path.isdir(mv_dir_1):
        os.mkdir(mv_dir_1)
    if not os.path.isdir(mv_dir_2):
        os.mkdir(mv_dir_2)
    file_path = os.path.join(data_dir, 'large.blob')
    if not os.path.isfile(file_path):
        generate_large_file(unit=unit, multiplier=multiplier)
    shutil.move(file_path, os.path.join(mv_dir_1, 'large.blob'))
    time.sleep(time_out)
    shutil.move(os.path.join(mv_dir_1, 'large.blob'), os.path.join(mv_dir_2, 'large.blob'))
    time.sleep(time_out)
    shutil.move(os.path.join(mv_dir_2, 'large.blob'), file_path)
    time.sleep(time_out)
    if remove:
        os.remove(file_path)
    log_copy.info("Finished copy with unit {}, multiplier {}, remove {}, time_out {} and uuid {}".format(
        unit, multiplier, remove, time_out, uid))


def ddot(iterations, time_out=1, modifiers=[0.9, 5, 2]):
    '''
    Executes dot product between 2  2D arrays whos size is determined by the L2 cache size.
    Simulates ALU and CPU interference
    :param iterations: Number of iterations to run, recommended 5 or less
    :param time_out: seconds between re-execution
    :param modifiers: list of modifiers to be randomly chosen from at each iteration
    :return:
    '''
    uid = uuid.uuid4()
    l2_cashe = int(cpuinfo.get_cpu_info()['l2_cache_size'])
    log_ddot.info("Started ddot with iteration {}, time_out {}, modifiers {}, L2CacheSize {} and uuid {}".format(
        iterations, time_out, modifiers, l2_cashe, uid))

    def compute_array_size(l2_cashe,
                           modifier=1):  # TODO find a more elegant solution
        size = 45
        if l2_cashe == 256:
            size = 181
        elif l2_cashe == 512:
            size = 256
        elif l2_cashe == 1024:
            size = 362
        elif l2_cashe == 2048:
            size = 512
        elif l2_cashe == 4096:
            size = 724
        elif l2_cashe == 8192:
            size = 1024
        elif l2_cashe == 16384:
            size = 1448
        elif l2_cashe == 32768:
            size = 2048
        elif l2_cashe > 32768:
            print("L2 cache to large, no presents found, defaulting to max value.")
            size = 2048
        elif l2_cashe < 256:
            print("L2 cache to small, no presents found, defaulting to min value.")
            size = 45
        return size * modifier
    asize = compute_array_size(l2_cashe)
    for it in range(1, iterations):
        modifier = random.choice(modifiers)
        asize = int(asize*modifier)
        log_ddot.info("Modifier of uuid {} for iteration {} out of {} is {}".format(uid, it, iterations, modifier))
        arr1 = np.random.rand(asize, asize)
        arr2 = np.random.rand(asize, asize)
        n_dot = np.dot(arr1, arr2)
        time.sleep(time_out)
        del arr1, arr2, n_dot
    log_ddot.info("Finished ddot with iteration {}, time_out {}, modifiers {}, L2CacheSize {} and uuid {}".format(
        iterations, time_out, modifiers, l2_cashe, uid))


if __name__ == '__main__':
    # settings = {'half': True,
    #             'time_out': 4}
    # cpu_overload(settings)
    # memeater()
    # memeater_v2(unit='gb', multiplier=1, iteration=2, time_out=20)
    # generate_large_file()
    copy(unit='kb', multiplier=4)
    # ddot(iterations=10)
