import logging
import logging.handlers
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
    if hasattr(settings, 'LOG_FORMAT'):
        formatter = logging.Formatter(settings.LOG_FORMAT)
    else:
        formatter = logging.Formatter('%(asctime)-15s [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s')

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
