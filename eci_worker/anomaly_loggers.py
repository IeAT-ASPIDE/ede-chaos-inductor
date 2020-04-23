import logging
from logging.handlers import RotatingFileHandler
import os


# Logging
def setup_logger(anomaly_name):
    log = logging.getLogger(anomaly_name)
    log.setLevel(logging.INFO)
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
    log_file_name = "{}-out.log".format(anomaly_name)
    handler = RotatingFileHandler(os.path.join(log_dir, log_file_name), maxBytes=100000000, backupCount=5)
    form = "%(created)f %(filename)13s:%(lineno)-4d\t%(levelname)-8s %(message)s"
    formatter = logging.Formatter(form)
    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log
