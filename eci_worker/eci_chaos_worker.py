#worker.py
from redis import Redis
from rq import Worker, Queue, Connection
from eci_worker import util

r_connection = Redis()
if __name__ == '__main__':
    config = util.load_yaml('worker.yaml')
    with Connection(connection=r_connection):
        worker = Worker(map(Queue, config['listen']))
        worker.work()
