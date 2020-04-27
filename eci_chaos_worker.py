# eci_chaos_worker.py
from redis import Redis
from rq import Worker, Queue, Connection
from eci_worker import util

r_connection = Redis()
if __name__ == '__main__':
    config = util.load_yaml('worker.yaml')
    with Connection(connection=r_connection):
        worker = Worker(map(Queue, config['listen']))
        pid_f = 'worker.pid'
        print('Saving pid {} to file {}'.format(worker.pid, pid_f))
        util.save_pid(worker.pid, pid_f)
        worker.work()
        print('Cleaning up ...')
        util.clean_up_pid(pid_f)