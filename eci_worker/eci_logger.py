import logging
from logging.handlers import RotatingFileHandler
import os
# Logging
log = logging.getLogger("eci")
log.setLevel(logging.INFO)
log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))

handler = RotatingFileHandler(os.path.join(log_dir, "eci-out.log"), maxBytes=10000, backupCount=5)
form = "%(created)f %(filename)13s:%(lineno)-4d\t%(levelname)-8s %(message)s"
# form2 = '[%(created)f]:[%(name)s]:[%(levelname)s] - %(message)s'
formatter = logging.Formatter(form)
handler.setFormatter(formatter)
consoleHandler = logging.StreamHandler()
log.addHandler(handler)
log.addHandler(consoleHandler)
# app.logger.addHandler(handler)




# logger = logging.getLogger("EDE Log")
# logger.setLevel(logging.INFO)
#
#
#
# # add a rotating handler
# logFile = os.path.join('ede.log')
# handler = RotatingFileHandler(logFile, maxBytes=100000000,  backupCount=5)
# logger.addHandler(handler)
# consoleHandler = logging.StreamHandler()
# logger.addHandler(consoleHandler)


