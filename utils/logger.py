import logging
from os import path

LOGGERS = {}
# [:-6] delete "/utils"
LOG_FILE = path_name = path.join(path.dirname(path.abspath(__file__).replace("/utils", "")), "static", "log.txt")
FORMATTER = logging.Formatter("%(asctime)s - %(module)s.%(funcName)s line %(lineno)s: %(message)s")


def get_logger(logger_name):
    global LOGGERS, LOG_FILE, FORMATTER
    if logger_name not in LOGGERS:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setFormatter(FORMATTER)
        logger.addHandler(ch)
        fh = logging.FileHandler(LOG_FILE)
        fh.setFormatter(FORMATTER)
        logger.addHandler(fh)
        LOGGERS[logger_name] = logger
    return LOGGERS[logger_name]
