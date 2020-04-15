import sys
import time
from rq import Connection, Worker
from redis import Redis

redis = Redis()


def need_burst_workers():
    # check database or redis key to determine whether burst worker army is required
    return True #boolean


def num_burst_workers_needed():
    # check the number, maybe divide the number of pending tasks by n
    return 10 #integer


def main(qs):
    with Connection(connection=redis):
        if need_burst_workers():
            [Worker(qs).work(burst=True) for i in range(num_burst_workers_needed())]
        else:
            time.sleep(10) #in seconds


if __name__ == '__main__':
    qs = sys.argv[1:] or ['default']
    main(qs)