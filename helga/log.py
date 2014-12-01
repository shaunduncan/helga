import logging
import logging.handlers
import os
import sys

from helga import settings


def getLogger(name):
    """
    Make some logger the same for all points in the app
    """
    level = getattr(settings, 'LOG_LEVEL', 'INFO')

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level, logging.INFO))
    logger.propagate = False

    # Setup the default handler
    if hasattr(settings, 'LOG_FILE') and settings.LOG_FILE:
        handler = logging.handlers.RotatingFileHandler(filename=settings.LOG_FILE,
                                                       maxBytes=50*1024*1024,
                                                       backupCount=6)
    else:
        handler = logging.StreamHandler()
        handler.stream = sys.stdout

    # Setup formatting
    if hasattr(settings, 'LOG_FORMAT') and settings.LOG_FORMAT:
        formatter = logging.Formatter(settings.LOG_FORMAT)
    else:
        formatter = logging.Formatter('%(asctime)-15s [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s')

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_channel_logger(channel):
    """
    Gets a logger with a TimedRotatingFileHandler that is suitable for
    channel logs
    """
    logger = logging.getLogger(u'channel_logger/{0}'.format(channel))
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Channel logs are grouped into directories by channel name
    log_dir = os.path.join(settings.CHANNEL_LOGGING_DIR, channel)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, 'log.txt')

    # Setup a daily rotating file handler
    handler = logging.handlers.TimedRotatingFileHandler(log_file, when='d', utc=True)
    handler.setFormatter(logging.Formatter(u'%(asctime)s - %(nick)s - %(message)s'))
    logger.addHandler(handler)

    return logger
