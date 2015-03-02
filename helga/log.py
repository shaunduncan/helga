"""
Logging utilities for helga
"""
import datetime
import logging
import logging.handlers
import os
import sys

from helga import settings


def getLogger(name):
    """
    Obtains a named logger and ensures that it is configured according to helga's log settings
    (see :ref:`helga.settings.logging`). Use of this is generally intended to mimic
    `logging.getLogger` with the exception that it takes care of formatters and handlers.

    :param name: The name of the logger to get
    """
    level = settings.LOG_LEVEL

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level, logging.INFO))
    logger.propagate = False

    # Setup the default handler
    if settings.LOG_FILE:
        handler = logging.handlers.RotatingFileHandler(filename=settings.LOG_FILE,
                                                       maxBytes=50*1024*1024,
                                                       backupCount=6)
    else:
        handler = logging.StreamHandler()
        handler.stream = sys.stdout

    # Setup formatting
    default_format = '%(asctime)-15s [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s'
    formatter = logging.Formatter(settings.LOG_FORMAT or default_format)

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_channel_logger(channel):
    """
    Obtains a python logger configured to operate as a channel logger.

    :param channel: the channel name for the desired logger
    """
    logger = logging.getLogger(u'channel_logger/{0}'.format(channel))
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.addFilter(UTCTimeLogFilter())

    # Channel logs are grouped into directories by channel name
    log_dir = os.path.join(settings.CHANNEL_LOGGING_DIR, channel)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Setup a daily rotating file handler
    handler = ChannelLogFileHandler(log_dir)
    handler.setFormatter(logging.Formatter(u'%(utctime)s - %(nick)s - %(message)s'))
    logger.addHandler(handler)

    return logger


class UTCTimeLogFilter(logging.Filter):
    """
    A log record filter that will add an attribute ``utcnow`` and ``utctime``
    to a log record. The former is a utcnow datetime object, the latter is
    the formatted time of day for utcnow.
    """

    def filter(self, record):
        """
        Filter the log record and add two attributes:

        * ``utcnow``: the value of `datetime.datetime.utcnow`
        * ``utctime``: the time formatted string of ``utcnow`` in the form ``HH:MM:SS``
        """
        record.utcnow = datetime.datetime.utcnow()
        record.utctime = record.utcnow.strftime('%H:%M:%S')
        return True


class ChannelLogFileHandler(logging.handlers.BaseRotatingHandler):
    """
    A rotating file handler implementation that will create UTC dated log files
    suitable for channel logging.
    """

    def __init__(self, basedir):
        """
        :param basedir: The base directory where logs should be stored
        """
        self.basedir = basedir
        filename = os.path.join(basedir, self.current_filename())
        self.next_rollover = self.compute_next_rollover()
        try:
            super(logging.handlers.BaseRotatingHandler, self).__init__(filename, 'a')
        except TypeError:  # pragma: no cover Python >= 2.7
            # python 2.6 uses old-style classes for logging.Handler
            logging.handlers.BaseRotatingHandler.__init__(self, filename, 'a')

    def compute_next_rollover(self):
        """
        Based on UTC now, computes the next rollover date, which will be 00:00:00
        of the following day. For example, if the current datetime is 2014-10-31 08:15:00,
        then the next rollover will be 2014-11-01 00:00:00.
        """
        now = datetime.datetime.utcnow()
        tomorrow = now + datetime.timedelta(days=1)
        return datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day)

    def current_filename(self):
        """
        Returns a UTC dated filename suitable as a log file. Example: 2014-12-15.txt
        """
        return datetime.datetime.utcnow().strftime('%Y-%m-%d.txt')

    def shouldRollover(self, record):
        """
        Returns True if the current UTC datetime occurs on or after the
        next scheduled rollover datetime. False otherwise.

        :param record: a python log record
        """
        return datetime.datetime.utcnow() >= self.next_rollover

    def doRollover(self):
        """
        Perform log rollover. Closes any open stream, sets a new log filename,
        and computes the next rollover time.
        """
        if self.stream:
            self.stream.close()
            self.stream = None

        self.baseFilename = os.path.abspath(os.path.join(self.basedir, self.current_filename()))
        self.stream = self._open()

        self.next_rollover = self.compute_next_rollover()
