import datetime
import logging
import logging.handlers
import os
import sys
import time

import pymongo

from helga import settings
from helga.db import db


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

    # If enabled, add the mongo backed handler
    if settings.CHANNEL_LOGGING_DB:
        logger.addHandler(DatabaseChannelLogHandler(channel))

    return logger


class DatabaseChannelLogHandler(logging.Handler):
    """
    A logging handler that will store channel logs in helga's Mongo database
    """

    def __init__(self, channel):
        self.channel = channel
        try:
            super(DatabaseChannelLogHandler, self).__init__(level=logging.INFO)
        except TypeError:  # pragma NO COVER Python >= 2.7
            # python 2.6 uses old-style classes for logging.Handler
            logging.Handler.__init__(self, level=logging.INFO)

    def createLock(self):
        """
        This handler requires no threading lock for I/O. That is handled by mongo.
        """
        self.lock = None

    def _ensure_indexes(self):
        """
        Ensure indexes exist. Note: message is not indexed since
        'text' indexes are not available until MongoDB 2.6 and may
        have performance overhead
        """
        # Channel only index
        db.channel_logs.ensure_index([
            ('channel', pymongo.ASCENDING),
            ('created', pymongo.DESCENDING)
        ])

        # Nick only index
        db.channel_logs.ensure_index([
            ('nick', pymongo.ASCENDING),
            ('created', pymongo.DESCENDING)
        ])

        # Channel+nick index
        db.channel_logs.ensure_index([
            ('nick', pymongo.ASCENDING),
            ('channel', pymongo.ASCENDING),
            ('created', pymongo.DESCENDING)
        ])

    def emit(self, record):
        """
        Stores a logged channel message in the database
        """
        if db is None:
            return

        created = time.mktime(datetime.datetime.utcnow().timetuple())

        db.channel_logs.insert({
            'channel': self.channel,
            'created': created,
            'nick': record.nick,
            'message': record.message,
        })

        self._ensure_indexes()
