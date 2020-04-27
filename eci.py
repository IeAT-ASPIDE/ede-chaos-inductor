from flask import Flask, send_file, Response, jsonify, request
from flask_restful import Api, Resource, abort
from functools import wraps
from flask_restful_swagger import swagger
# import logging
# from logging.handlers import RotatingFileHandler
from eci_worker.eci_logger import log, handler
import os
from redis import Redis
import rq
from rq.job import Job
from rq.registry import StartedJobRegistry
from eci_worker.anomalies import dummy, example, cpu_overload, memeater_v2, ddot
from eci_worker.eci_chaos_gen import ChaosGen
from eci_worker.eci_app import app, api
from eci_worker.util import load_sx
import psutil
import platform

etc_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc'))
log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
# print(etc_dir)


# App, Api and custom error handling
# app = Flask('eci')
# handle_exception = app.handle_exception
# handle_user_exception = app.handle_user_exception
# api = swagger.docs(Api(app), apiVersion='0.1')
# # api = Api(app)
# app.handle_exception = handle_exception
# app.handle_user_exception = handle_user_exception
#
# # Logging
# app.logger.addHandler(handler)
# # log = logging.getLogger("eci")


# Redis and rq
# r_connection = Redis.from_url('redis://')
r_connection = Redis()
queue = rq.Queue('test', connection=r_connection)  # TODO create 3 priority queues and make them selectable from REST call
chaosgen = ChaosGen(r_connection=r_connection, queue=queue)


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.headers['x-access-tokens'] != load_sx():
            return jsonify({'resp': 'failed token'})
        return f(*args, **kwargs)
    return decorated_function


class NodeDescriptor(Resource):
    def get(self):
        uname = platform.uname()
        cpufreq = psutil.cpu_freq()
        svmem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk_usage = psutil.disk_usage('/').total
        response = jsonify({
            'system': uname.system,
            'node': uname.node,
            'release': uname.release,
            'version': uname.version,
            'machine': uname.machine,
            'processor': {
                'type': uname.processor,
                'cores_physical':  psutil.cpu_count(logical=False),
                'cores_logical':  psutil.cpu_count(logical=True),
                'frequency_max': cpufreq.max,
                'frequency_min': cpufreq.min,
                'frequency_current': cpufreq.current,
            },
            'memory': {
                'total': svmem.total,
                'swap': swap.total
            },
            'disk': disk_usage,
        })
        response.status_code = 200
        return response


class GetLogs(Resource):
    def get(self):
        log = os.path.join(log_dir, 'eci-out.log')
        return send_file(log, mimetype='text/plain')


class ListAnomalyInducers(Resource):
    def get(self):
        log.info("Logging Initialized")
        return "nothing yet"


class AnomalyInducer(Resource):
    def get(self, anomaly_id):
        return 'you have set {}'.format(anomaly_id)


class TaskExample(Resource):
    def get(self):
        job = queue.enqueue(example, 100)
        response = jsonify({"job_id": job.get_id()})
        response.status_code = 201
        return response


class TaskExampleDetails(Resource):
    def get(self, job_id):
        try:
            job = Job.fetch(job_id, connection=r_connection)
        except Exception as inst:
            log.error("No job with id {}".format(job_id))
            response = jsonify({'error': 'no such job'})
            response.status_code = 404
            return response
        job.refresh()
        status = job.get_status()
        finished = job.is_finished
        meta = job.meta
        response = jsonify({'status': status,
                            'finished': finished,
                            'meta': meta})
        response.status_code = 200
        return response


class CPUOverload(Resource):
    def get(self):
        job = queue.enqueue(cpu_overload, 1)
        response = jsonify({"job_id": job.get_id()})
        response.status_code = 201
        return response


class MemEater(Resource):
    def get(self):
        settings = {'unit': 'gb', 'multiplier': 1, 'iteration': 2, 'time_out': 20}
        job = queue.enqueue(memeater_v2, **settings)
        response = jsonify({"job_id": job.get_id()})
        response.status_code = 201
        return response


class ChaosGenSessionDefiner(Resource):
    def get(self):
        response = jsonify(chaosgen.get_defined_session())
        response.status_code = 200
        return response

    def put(self):
        if not request.is_json:
            response = jsonify({"error": 'session must be JSON'})
            response.status_code = 415
            return response
        chaosgen.define_session(request.json)
        log.info("New session definition received")
        response = jsonify(request.json)
        response.status_code = 201
        return response


class ChaosGenSessionExecutor(Resource):
    def get(self):
        response = jsonify(chaosgen.get_schedueled_session())
        response.status_code = 200
        return response

    def put(self):
        session = chaosgen.session_gen()
        chaosgen.set_schedueled_session(session)
        response = jsonify({"session": session})
        response.status_code = 201
        return response

    @token_required
    def post(self):
        if not chaosgen.schedueled_session:
            log.warning("No user defined session data defined, using default!")
        chaosgen.job_gen()
        response = jsonify(chaosgen.get_detailed_session())
        response.status_code = 201
        return response
            # response = jsonify({"error": "No user defined session data defined"})
            # response.status_code = 500
            # return response


class ChaosGenSessionJobs(Resource):
    def get(self):
        response = jsonify({'jobs': chaosgen.get_schedueled_jobs_rq()})
        response.status_code = 200
        return response

    def delete(self):
        resp = chaosgen.remove_all_jobs()
        response = jsonify(resp)
        if 'error' in resp.keys():
            response.status_code = 404
        else:
            response.status_code = 200
        return response


class ChaosGenSessionJob(Resource):
    def get(self, job_id):
        if job_id == 'all':
            response = jsonify(chaosgen.get_detailed_session())
            response.status_code = 200
            return response
        resp = chaosgen.return_jobs_status(job_id=job_id)
        response = jsonify(resp)
        if 'error' in resp.keys():
            response.status_code = 404
        else:
            response.status_code = 200
        return response

    def delete(self, job_id):
        resp = chaosgen.remove_job(job_id=job_id)
        response = jsonify(resp)
        if 'error' in resp.keys():
            response.status_code = 404
        else:
            response.status_code = 200
        return response


class ChaosGenSessionListAnoLogs(Resource):
    def get(self):
        response = jsonify({'logs': os.listdir(log_dir)})
        response.status_code = 200
        return response


class ChaosGenSessionAnoLogs(Resource):
    def get(self, ano_log):
        log = os.path.join(log_dir, ano_log)
        if not os.path.isfile(log):
            response = jsonify({'error': "missing log {}".format(log)})
            response.status_code = 404
            return response
        return send_file(log, mimetype='text/plain')


class GetAllTaks(Resource):
    def get(self):
        registry = StartedJobRegistry(queue=queue, connection=r_connection)
        running_job_ids = registry.get_job_ids()  # Jobs which are exactly running.
        expired_job_ids = registry.get_expired_job_ids()
        response = jsonify({'running': running_job_ids,
                            'expired': expired_job_ids})
        response.status_code = 200
        return response


api.add_resource(ChaosGenSessionDefiner, '/chaos/session')
api.add_resource(ChaosGenSessionExecutor, '/chaos/session/execute')
api.add_resource(ChaosGenSessionJobs, '/chaos/session/execute/jobs')
api.add_resource(ChaosGenSessionJob, '/chaos/session/execute/jobs/<job_id>')
api.add_resource(ChaosGenSessionListAnoLogs, '/chaos/session/execute/jobs/logs')
api.add_resource(ChaosGenSessionAnoLogs, '/chaos/session/execute/jobs/logs/<ano_log>')


api.add_resource(MemEater, '/memeater')
api.add_resource(NodeDescriptor, '/node')
api.add_resource(GetAllTaks, '/registry')
api.add_resource(TaskExampleDetails, '/task/<job_id>')
api.add_resource(TaskExample, '/task')
api.add_resource(CPUOverload, '/cpu_overload')
api.add_resource(ListAnomalyInducers, '/inducers')
api.add_resource(AnomalyInducer, '/inducers/<anomaly_id>')
api.add_resource(GetLogs, '/logs')


"""
Custom errot Handling

"""

def forbidden(e):
    response = jsonify({'error': 'forbidden'})
    response.status_code = 403
    return response


def page_not_found(e):
    response = jsonify({'error': 'not found'})
    response.status_code = 404
    return response


def internal_server_error(e):
    response = jsonify({'error': 'internal server error'})
    response.status_code = 500
    return response


def meth_not_allowed(e):
    response = jsonify({'error': 'method not allowed'})
    response.status_code = 405
    return response


def bad_request(e):
    response = jsonify({'error': 'bad request'})
    response.status_code = 400
    return response


def bad_mediatype(e):
    response = jsonify({'error': 'unsupported media type'})
    response.status_code = 415
    return response


app.register_error_handler(404, page_not_found)
app.register_error_handler(403, forbidden)
app.register_error_handler(500, internal_server_error)
app.register_error_handler(405, meth_not_allowed)
app.register_error_handler(400, bad_request)
app.register_error_handler(415, bad_mediatype)


if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)
