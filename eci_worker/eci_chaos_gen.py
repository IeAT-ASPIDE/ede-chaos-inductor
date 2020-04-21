import logging
import random
import numpy as np
from scipy.stats import norm
from importlib import import_module
import rq
from redis import Redis
from eci_worker.anomalies import *
logger = logging.getLogger(__name__)
log = logger.getChild('ChaosGen')


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
        self.running = []
        self.finished = []
        self.failed = []
        self.schedueled = []
        self.schedueled_session = []

    def _session_gen(self):
        if self.session is None:
            log.warning("No session data received, using default")
            sgen = self.session
        else:
            self.session = session
            sgen = session

        options = sgen.get('options', None)
        anomalies = sgen.get('anomalies', None)
        if options is not None:
            self.loop = options.get('loop', False)
            self.randomise = options.get('randomise', False)
            self.distribution = options.get('distribution', False)
            self.sample_size = options.get('sample_size', len(anomalies))
        # print(anomalies)
        if self.randomise:
            random.shuffle(anomalies)
            # sgen = anomalies
        if self.distribution == 'uniform':
            sgen = list(np.random.choice(anomalies, self.sample_size))
            # print(len(np.random.choice(anomalies, self.sample_size)))
        elif self.distribution == 'prob':
            prob_list = []
            for ano in anomalies:
                prob_list.append(ano['prob'])
            sum_prob = sum(prob_list)
            if round(sum_prob, 2) < 1.0 or round(sum_prob, 2) > 1.0:
                print("Probabilities sum to {}, have to be 1.0".format(sum_prob))
                import sys
                sys.exit()
            sgen = list(np.random.choice(anomalies, self.sample_size, p=prob_list))

        # print(anomalies)
        # print(len(anomalies))
        # print(options)
        self.schedueled_session = sgen
        return sgen

    def job_gen(self):
        jobs = self._session_gen()
        mod = import_module(self.anomaly_def)
        print(mod)
        for rjob in jobs:
            ano_inst = getattr(mod, rjob['type'])
            job = self.queue.enqueue(ano_inst, **rjob['options'])
            id = job.get_id()
            # print(ano_inst)
            print("Queued anomaly {} with params {} and  id {}".format(rjob['type'], rjob['options'], id))
            self.schedueled.append(id)

    def _get_schedueled_jobs(self):
        return self.schedueled

    def _get_session(self):
        return self.schedueled_session


if __name__ == '__main__':
    r_connection = Redis()
    queue = rq.Queue('test',
                     connection=r_connection)
    session = {
  "anomalies": [
    {
      "type": "dummy",
      "options": {
        "stime": 10
      },
      "prob": 0.4
    },
    {
      "type": "cpu_overload",
      "options": {
        "half": 1,
        "time_out": 15
      },
      "prob": 0.1
    },
    {
      "type": "memeater_v2",
      "options": {
        "unit": "gb",
        "multiplier": 1,
        "iteration": 2,
        "time_out": 20
      },
      "prob": 0.2
    },
    {
      "type": "copy",
      "options": {
         "unit": "kb",
        "multiplier": 1,
        "remove": 1,
        "time_out": 20
      },
      "prob": 0.2
    },
    {
      "type": "ddot",
      "options": {
        "iterations": 1,
        "time_out": 1,
        "modifiers": [0.9, 5,  2]
      },
      "prob": 0.1
    }
  ],
  "options":
  {
    "loop": 1,
    "randomise": 1,
    "sample_size": 10,
    "distribution": "prob"
  }
}

    test_gen = ChaosGen(r_connection=r_connection, queue=queue, session=session)
    t = test_gen._session_gen()
    test_gen.job_gen()
    print(test_gen._get_schedueled_jobs())
    print(test_gen._get_session())
    # print(np.random.uniform(low=0.1, high=np.nextafter(1, 2), size=1))
