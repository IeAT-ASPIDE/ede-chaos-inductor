import requests
import asyncio
import aiohttp
import time
from eci_control.eci_control_log import log, log_dir
import sys
import random
import os, getopt


class EciCommand():
    log.info("Starting ECI control ...")

    def __init__(self, node_list, token, port=5000):
        self.node_list = node_list
        self.port = port
        self.header = self._set_header(token)
        self.session = None
        self.workers = 1

    def _set_header(self, token):
        log.info("Token is set")
        return {"x-access-tokens": token}

    def get_nodes(self):
        return self.node_list

    def append_node(self, node):
        log.info("Appended node {} to eci".format(node))
        self.node_list.append(node)

    def get_port(self):
        return self.port

    def set_port(self, port):
        log.info("Port for eci workers set to {}".format(port))
        self.port = port

    def gen_url_node_info(self):
        '''
        :return: resources to fetch node information
        '''
        node_request = []
        for node in self.node_list:
            url = "http://{}:{}/node".format(node, self.port)
            node_request.append(url)
        return node_request

    def gen_node_info(self):
        log.info('Generating node info urls')
        response = {}
        for node in self.node_list:
            url = "http://{}:{}/node".format(node, self.port)
            r = requests.get(url=url)
            response[node] = r.json()
        return response

    def get_chaos_session(self):
        '''
        :return: resource to fetch currently set session information
        '''
        node_request = []
        for node in self.node_list:
            url = "http://{}:{}/chaos/session".format(node, self.port)
            node_request.append(url)
        return node_request

    def gen_url_node_worker(self):
        '''
        :return: resources to fetch worker urls
        '''
        log.info('Generating worker info urls')
        node_request = []
        for node in self.node_list:
            url = "http://{}:{}/workers".format(node, self.port)
            node_request.append(url)
        return node_request

    def gen_urls_chaos_session_execute(self):
        log.info('Generating chaos session execute urls')
        node_request = []
        for node in self.node_list:
            url = "http://{}:{}/chaos/session/execute".format(node, self.port)
            node_request.append(url)
        return node_request

    def gen_session_execute_info(self):
        log.info('Generating chaos session execute status urls')
        node_request = []
        for node in self.node_list:
            url = "http://{}:{}/chaos/session/execute/jobs".format(node, self.port)
            node_request.append(url)
        return node_request

    def sequential_put(self, node_urls, payload=None):
        for node in node_urls:
            d_header = self.header
            d_header['content-type'] = 'application/json'
            s = requests.Session()
            s.headers.update({'content-type': 'application/json'})
            # print(s.headers.get())
            r = s.put(node, json=payload)
            print(r.json())

    def parallel_node_get(self, node_urls):
        log.info('Executing async get ...')
        # node_request = self._gen_url_node()
        async def get_eci(url):
            log.info('Starting {}'.format(url))
            response = await aiohttp.ClientSession().get(url)
            data = await response.json()
            log.debug('{}: {} bytes: {}'.format(url, len(data), data))
            return data

        futures = [get_eci(url) for url in node_urls]
        loop = asyncio.get_event_loop()
        done, _ = loop.run_until_complete(asyncio.wait(futures))
        responses = []
        for res in done:
            log.info(res.result())
            responses.append(res.result())
        return {'responses': responses}

    def parallel_node_put(self, node_urls, payload=None):
        log.info('Executing async put ...')

        async def put_eci(url, payload=payload):
            log.info('Starting {}'.format(url))
            if payload is None:
                response = await aiohttp.ClientSession().put(url,
                                                              headers=self.header)
            else:
                d_header = self.header
                d_header['Content-Type'] = 'application/json'
                response = await aiohttp.ClientSession().put(url,
                                                              json=payload,
                                                              headers=d_header)
            data = await response.json()
            log.debug('{}: {} bytes: {}'.format(url, len(data), data))
            return data

        futures = [put_eci(url) for url in node_urls]
        loop = asyncio.get_event_loop()
        done, _ = loop.run_until_complete(asyncio.wait(futures))
        responses = []
        for res in done:
            log.info(res.result())
            responses.append(res.result())
        return {'responses': responses}

    def parallel_node_post(self, node_urls, payload=None):
        log.info('Executing async post ...')

        async def post_eci(url, payload=payload):
            log.info('Starting {}'.format(url))
            if payload is None:
                response = await aiohttp.ClientSession().post(url,
                                                             headers=self.header)
            else:
                d_header = self.header
                d_header["Content-Type"] = "application/json"
                # print(d_header)
                response = await aiohttp.ClientSession().post(url,
                                                             json=payload,
                                                             headers=d_header)
            data = await response.json()
            log.debug('{}: {} bytes: {}'.format(url, len(data), data))
            return data

        futures = [post_eci(url) for url in node_urls]
        loop = asyncio.get_event_loop()
        done, _ = loop.run_until_complete(asyncio.wait(futures))
        responses = []
        for res in done:
            log.info(res.result())
            responses.append(res.result())
        return {'responses': responses}

    def parallel_node_delete(self, node_urls, payload=None):
        log.info('Executing async delete ...')

        async def delete_eci(url, payload=payload):
            log.info('Starting {}'.format(url))
            if payload is None:
                response = await aiohttp.ClientSession().delete(url,
                                                              headers=self.header)
            else:
                d_header = self.header
                d_header['Content-Type'] = 'application/json'
                response = await aiohttp.ClientSession().delete(url,
                                                              json=payload,
                                                              headers=d_header)
            data = await response.json()
            log.debug('{}: {} bytes: {}'.format(url, len(data), data))
            return data

        futures = [delete_eci(url) for url in node_urls]
        loop = asyncio.get_event_loop()
        done, _ = loop.run_until_complete(asyncio.wait(futures))
        responses = []
        for res in done:
            log.info(res.result())
            responses.append(res.result())
        return {'responses': responses}

    def add_session(self, session):
        log.info("Added new session info")
        self.session = session

    def get_session(self):
        return self.session

    def set_workers(self, workercount):
        log.info("Worker count set to {}".format(workercount))
        self.workers = workercount

    def check_workers(self):
        # Check the number of workers set vs running
        return 0

    def start_workers(self):
        # start the number of workers set
        return 0

    def validate_session(self):
        log.warning("Validation not working!")  # Todo implement session validation
        return self.session

    def get_all_logs(self):
        for node in self.node_list:
            url_node = "http://{}:{}/node".format(node, self.port)
            url_logs = "http://{}:{}/chaos/session/execute/jobs/logs".format(node, self.port)
            r1 = requests.get(url=url_node)
            node_name = r1.json()['node']
            log.info('Fetching logs from {}'.format(node_name))
            r2 = requests.post(url=url_logs)
            file_name = os.path.join(log_dir, "logs_{}.zip".format(node_name))
            log.info('Saving logs from {} to {}'.format(node_name, file_name))
            with open(file_name, 'wb') as fd:
                fd.write(r2.content)

    def execute_session(self, check_interval=15):
        if self.session is None:
            log.error("No session information given! Existing")
            sys.exit(1)

        elif "anomalies" in self.session.keys():
            log.info("Detected unique session config")
            eci_session = self.session
            node_worker_urls = self.gen_url_node_worker()
            worker_count = eci_session['options'].pop('workers')
            log.info('worker count is set to {}'.format(worker_count))
            resp_workers = self.parallel_node_get(node_urls=node_worker_urls)
            # Checking number of workers needed and started
            restart_workers = False
            for resp_worker in resp_workers['responses']:
                if len(resp_worker['workers']) != worker_count:
                    restart_workers = True
            # If worker count is different the actua worker count start over
            log.info('Worker restart is {}'.format(restart_workers))
            if restart_workers:
                log.info("Stopping all workers ...")
                self.parallel_node_delete(node_urls=node_worker_urls)
                for i in range(worker_count):
                    log.info('Starting worker {} for all nodes ...'.format(i+1))
                    self.parallel_node_post(node_urls=node_worker_urls)

            # Send session info
            nodes_session = self.get_chaos_session()
            self.parallel_node_get(node_urls=nodes_session)
            self.parallel_node_put(node_urls=nodes_session, payload=eci_session)

            # Generate new session
            node_session_execute = self.gen_urls_chaos_session_execute()
            self.parallel_node_put(node_urls=node_session_execute)

            # Start execution
            self.parallel_node_post(node_urls=node_session_execute)
            time.sleep(1)
            # Get execution info
            node_session_execute = self.gen_session_execute_info()
            log.warning("Session execution started at {}").format(time.time())
            running = True

            while running:
                r = self.parallel_node_get(node_urls=node_session_execute)
                for resp in r['responses']:
                    print("Failed: -> {}".format(len(resp['jobs']['failed'])))
                    print("finished: -> {}".format(len(resp['jobs']['finished'])))
                    print("queued: -> {}".format(len(resp['jobs']['queued'])))
                    print("started: -> {}".format(len(resp['jobs']['started'])))
                    if len(resp['jobs']['queued']) == 0:
                        running = False
                    time.sleep(check_interval)

            log.warning('Session execution finished at {}'.format(time.time()))
        else:
            log.info("Detected custom session configs")
            sys.exit(0) # TODO implement custom config per node basis

    # def get_session(self):

    def loop_execute(self, ctime, staggeg_list=[10, 5, 7, 20, 15]):
        '''
        Execute while timeout time is not met
        :param ctime:
        :return:
        '''

        stagger = random.choice(staggeg_list)
        timeout = time.time() + 60 * ctime  # time minutes from now
        log.warning("Started execution of loop at {}".format(time.time()))
        log.info("Endtime set to {}".format(timeout))
        log.info("Stagger set to {} minutes".format(stagger))
        while True:
            if time.time() > timeout:
                break
            # print(time.time())
            # print(timeout)
            self.execute_session()
            time.sleep(60*stagger)
        log.warning("Finished execution of loop at {}".format(time.time()))


def main(argv,
         cluster,
         client):

    file_loc = None
    try:
        opts, args = getopt.getopt(argv, "he:tf:m:vx:d:lq:", ["endpoint=", "file=", "method=", "export=", "detect=",
                                                              "query="])  # todo:expand comand line options
    except getopt.GetoptError:
        log.warning('Invalid argument detected')
        print("eci_cnc.py -f <filelocation>")
        sys.exit(0)
    for opt, arg in opts:
        if opt == '-h':
            print("#" * 100)
            print("H2020 ASPIDE")
            print('Event Detection Engine Chaos Inducer')
            print("-" * 100)
            print('Utilisation:')
            print('-f -> chaos session configuration file')
            print("#" * 100)
            sys.exit(0)
        elif opt in ("-f", "--file"):
            file_loc = arg
        else:
            log.error("Unknown argument {}".format(opt))


if __name__ == "__main__":
    node_list = []
    port = 5000
    token = ""

    payload = {
        "anomalies": [
            {
                  "type": "dummy",
                  "options": {
                    "stime": 10
                  },
                  "prob": 0.20
                },
            {
                "type": "dummy",
                "options": {
                    "stime": 10
                },
                "prob": 0.05
            },
            {
                "type": "cpu_overload",
                "options": {
                    "half": 1,
                    "time_out": 35
                },
                "prob": 0.50
            },
            {
                "type": "dummy",
                "options": {
                    "stime": 10
                },
                "prob": 0.25
            }
        ],
        "options":
          {
            "loop": 1,
            "randomise": 1,
            "stagger_time": 0,
            "sample_size": 5,
            "distribution": "prob",
            "workers": 1
          }
    }
    eci = EciCommand(node_list=node_list, token=token, port=port)

    # fetching all logs
    eci.get_all_logs()

    sys.exit(0)
    # Adding session information
    eci.add_session(payload)

    # Execute session
    eci.execute_session()


    # Loop Execute session until ctime
    # ctime = 1
    # eci.loop_execute(ctime)

    # Get session execution (job) status
    node_session_execute = eci.gen_session_execute_info()
    r = eci.parallel_node_get(node_urls=node_session_execute)
    for resp in r['responses']:
        print("Failed: -> {}".format(len(resp['jobs']['failed'])))
        print("finished: -> {}".format(len(resp['jobs']['finished'])))
        print("queued: -> {}".format(len(resp['jobs']['queued'])))
        print("started: -> {}".format(len(resp['jobs']['started'])))


    # print(eci.gen_node_info())
    node_info_urls = eci.gen_url_node_info()
    eci.parallel_node_get(node_urls=node_info_urls)

    node_worker_urls = eci.gen_url_node_worker()

    # Check workers
    eci.parallel_node_get(node_urls=node_worker_urls)

    # Start workers
    eci.parallel_node_post(node_urls=node_worker_urls)

    # Stop workers
    # eci.parallel_node_delete(node_urls=node_worker_urls)

    time.sleep(1)
    # Check workers
    eci.parallel_node_get(node_urls=node_worker_urls)

    # Get chaos session from nodes
    nodes_session = eci.get_chaos_session()
    eci.parallel_node_get(node_urls=nodes_session)

    # Upload new payload
    eci.parallel_node_put(node_urls=nodes_session, payload=payload)
    # print(payload)
    # print(nodes_session)
    # eci.sequential_put(node_urls=nodes_session, payload=payload)

    # Generate new sessions in nodes
    node_session_execute = eci.gen_urls_chaos_session_execute()
    eci.parallel_node_put(node_urls=node_session_execute)
    #
    # Check new sessions from nodes
    eci.parallel_node_get(node_urls=node_session_execute)

    # time.sleep(3)
    # Execute session
    eci.parallel_node_post(node_urls=node_session_execute)


