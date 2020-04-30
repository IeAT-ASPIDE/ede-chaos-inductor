import logging
import random
import numpy as np
from scipy.stats import norm
from importlib import import_module
import rq
from rq.job import Job
from rq.registry import StartedJobRegistry
from redis import Redis
# from flask import jsonify
from eci_worker.anomalies import *
from eci_worker.eci_logger import log
from eci_worker.eci_app import app

class ChaosGen():
    def __init__(self, r_connection, queue, session=None):
        self.session = session
        self.r_connection = r_connection
        self.queue = queue
        self.loop = False
        self.randomise = False
        self.distribution = False
        self.anomaly_def = 'eci_worker.anomalies'
        self.session = {
            "anomalies": [
                {
                    "type": "dummy",
                    "options": {
                        "stime": 10
                    }
                },
                {
                    "type": "cpu_overload",
                    "options": {
                        "half": 1,
                        "time_out": 15
                    }
                },
                {
                    "type": "memeater_v2",
                    "options": {
                        "unit": "gb",
                        "multiplier": 1,
                        "iteration": 2,
                        "time_out": 20
                    }
                },
                {
                    "type": "copy",
                    "options": {
                        "unit": "kb",
                        "multiplier": 1,
                        "remove": 1,
                        "time_out": 20
                    }
                },
                {
                    "type": "ddot",
                    "options": {
                        "iterations": 1,
                        "time_out": 1,
                        "modifiers": [0.9, 5, 2]
                    }
                }
            ],
            "options":
                {
                    "loop": 1,
                    "randomise": 1,
                    "distribution": 0
                }
        }
        self.stagger_time = 300
        self.running = []
        self.finished = []
        self.failed = []
        self.jqueued = []
        self.started = []
        self.schedueled = []
        self.schedueled_session = []
        self.detailed_session_info = {}

    def define_session(self, session):
        log.info("New session raw defined")
        self.session = session

    def _intersperse(self, sgen, item):
        result = [item] * (len(sgen) * 2 - 1)
        result[0::2] = sgen
        return result

    def session_gen(self):
        sgen = self.session
        log.info("Detailed session generation started")
        options = sgen.get('options', None)
        anomalies = sgen.get('anomalies', None)
        if options is not None:
            self.loop = options.get('loop', False)
            self.randomise = options.get('randomise', False)
            self.distribution = options.get('distribution', False)
            self.sample_size = options.get('sample_size', len(anomalies))
            self.stagger_time = options.get('stagger_time', 0)
        # print(anomalies)
        if self.randomise:
            log.info("Session is randomised")
            random.shuffle(anomalies)
            # sgen = anomalies
        if self.distribution == 'uniform':
            log.info("Session uniform distribution")
            sgen = list(np.random.choice(anomalies, self.sample_size))
            # print(len(np.random.choice(anomalies, self.sample_size)))
        elif self.distribution == 'prob':
            log.info("Session probabilistic distribution")
            prob_list = []
            for ano in anomalies:
                prob_list.append(ano['prob'])
            sum_prob = sum(prob_list)
            if round(sum_prob, 2) < 1.0 or round(sum_prob, 2) > 1.0:
                log.error("Probabilities sum to {}, have to be 1.0".format(sum_prob))
                import sys
                sys.exit()
            sgen = list(np.random.choice(anomalies, self.sample_size, p=prob_list))
        else:
            sgen = anomalies

        if self.stagger_time:
            log.info("Stagger set to {}".format(self.stagger_time))
            stagger = {'type': 'dummy', 'options': {'stime': self.stagger_time, 'silent': 1}}
            sgen = self._intersperse(sgen=sgen, item=stagger)

        # print(anomalies)
        # print(len(anomalies))
        # print(options)
        self.schedueled_session = sgen
        log.info("Finished final session generation")
        return sgen

    def job_gen(self):
        if not self.schedueled_session:
            jobs = self.session_gen()
        else:
            jobs = self.schedueled_session
        mod = import_module(self.anomaly_def)
        # print(mod)
        log.info("Defined jobs: {}".format(jobs))
        for rjob in jobs:
            ano_inst = getattr(mod, rjob['type'])
            job = self.queue.enqueue(ano_inst, **rjob['options'])
            id = job.get_id()
            # print(ano_inst)
            log.info("Queued anomaly {} with params {} and  id {}".format(rjob['type'], rjob['options'], id))
            self.detailed_session_info[id] = {'anomaly': rjob['type'], 'options': rjob['options']}
            self.schedueled.append(id)

    def _get_schedueled_jobs(self):
        return self.schedueled

    def get_schedueled_jobs_rq(self):
        jobs = self.queue.get_job_ids()
        self.failed = self.queue.failed_job_registry.get_job_ids()
        self.jqueued = []
        self.started = self.queue.started_job_registry.get_job_ids()
        self.finished = self.queue.finished_job_registry.get_job_ids()
        for rjob in jobs:
            try:
                job = Job.fetch(rjob, connection=self.r_connection)
            except:
                log.error("No job with id {}".format(rjob))
                response = {'error': 'no such job'}
                return response
            if job.is_finished:
                self.finished.append(rjob)
            elif job.is_failed:
                self.failed.append(rjob)
            elif job.is_started:
                self.started.append(rjob)
            elif job.is_queued:
                self.jqueued.append(rjob)

        response = {
            'started': self.started,
            'finished': self.finished,
            'failed': self.failed,
            'queued':self.jqueued
        }

        return response

    def get_schedueled_session(self):
        return self.schedueled_session

    def set_schedueled_session(self, session):
        self.schedueled_session = session

    def get_defined_session(self):
        log.warning("Queried defined session")
        return self.session

    def get_detailed_session(self):
        return self.detailed_session_info

    def return_jobs_status(self, job_id):
        try:
            job = Job.fetch(job_id, connection=self.r_connection)
        except Exception as inst:
            log.error("No job with id {}".format(job_id))
            response = {'error': 'no such job'}
            return response
        job.refresh()
        status = job.get_status()
        finished = job.is_finished
        meta = job.meta
        response = {'status': status,
                            'finished': finished,
                            'meta': meta}
        return response

    def remove_job(self, job_id):
        try:
            job = Job.fetch(job_id, connection=self.r_connection)
        except Exception as inst:
            log.error("No job with id {}".format(job_id))
            response = {'error': 'no such job'}
            return response
        job.delete()
        log.info("Job with id {} deleted.".format(job_id))
        response = {"status": "deleted",
                    "job": job_id}
        return response

    def remove_all_jobs(self):
        jobs = self.queue.get_job_ids()
        for rjob in jobs:
            try:
                job = Job.fetch(rjob, connection=self.r_connection)
                job.delete()
                log.info("Deleted job with id {}".format(rjob))
            except:
                log.error("No job with id {}".format(rjob))
                response = {'error': 'no such job'}
                return response
        response = {'deleted_job': jobs}
        return response


if __name__ == '__main__':
    r_connection = Redis()
    queue = rq.Queue('test',
                     connection=r_connection)
#     session = {
#   "anomalies": [
#     {
#       "type": "dummy",
#       "options": {
#         "stime": 10
#       },
#       "prob": 0.4
#     },
#     {
#       "type": "cpu_overload",
#       "options": {
#         "half": 1,
#         "time_out": 15
#       },
#       "prob": 0.1
#     },
#     {
#       "type": "memeater_v2",
#       "options": {
#         "unit": "gb",
#         "multiplier": 1,
#         "iteration": 2,
#         "time_out": 20
#       },
#       "prob": 0.2
#     },
#     {
#       "type": "copy",
#       "options": {
#          "unit": "kb",
#         "multiplier": 1,
#         "remove": 1,
#         "time_out": 20
#       },
#       "prob": 0.2
#     },
#     {
#       "type": "ddot",
#       "options": {
#         "iterations": 1,
#         "time_out": 1,
#         "modifiers": [0.9, 5,  2]
#       },
#       "prob": 0.1
#     }
#   ],
#   "options":
#   {
#     "loop": 1,
#     "randomise": 1,
#     "sample_size": 10,
#     "distribution": "prob"
#   }
# }
    session = {
        "anomalies": [
            {
                  "type": "dummy",
                  "options": {
                    "stime": 10
                  },
                  "prob": 0.25
                },
            {
                "type": "dummy",
                "options": {
                    "stime": 10
                },
                "prob": 0.25
            },
            {
                "type": "dummy",
                "options": {
                    "stime": 10
                },
                "prob": 0.25
            },
            {
                "type": "dummy",
                "options": {
                    "stime": 10
                },
                "prob": 0.25
            },
        ],
        "options":
          {
            "loop": 1,
            "randomise": 1,
            "sample_size": 10,
            "distribution": "prob"
          }
    }

    # print(queue.finished_job_registry.get_job_ids())

    test_gen = ChaosGen(r_connection=r_connection, queue=queue, session=session)
    t = test_gen.session_gen()
    print(t)
    # test_gen.job_gen()
    # print(test_gen._get_schedueled_jobs())
    # print(test_gen._get_session())
    # # time.sleep(15)
    # print(test_gen.get_schedueled_jobs_rq())
    # print(test_gen.return_jobs_status(test_gen._get_schedueled_jobs()[0]))
    # # print(np.random.uniform(low=0.1, high=np.nextafter(1, 2), size=1))
    # print(test_gen.get_detailed_session())
