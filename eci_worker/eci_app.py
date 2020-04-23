from flask import Flask, send_file, Response, jsonify, request
from flask_restful import Api, Resource, abort
from flask_restful_swagger import swagger
from eci_worker.eci_logger import log, handler, consoleHandler

# App, Api and custom error handling
app = Flask('eci')
handle_exception = app.handle_exception
handle_user_exception = app.handle_user_exception
api = swagger.docs(Api(app), apiVersion='0.1')
# api = Api(app)
app.handle_exception = handle_exception
app.handle_user_exception = handle_user_exception

# Logging
app.logger.addHandler(handler)
# app.logger.addHandler(consoleHandler)
# log = logging.getLogger("eci")