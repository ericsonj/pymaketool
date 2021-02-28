import logging
from logging import Logger, NOTSET
import os

FORMATTER = logging.Formatter("%(levelname)-8s%(filename)s:%(lineno)d  %(message)s")

def getLogger(name='Log'):
    log = Logger.manager.getLogger(name)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(FORMATTER)
    log.addHandler(console_handler)
    log.setLevel(os.environ.get('LOGLEVEL', 'NOTSET'))
    return log