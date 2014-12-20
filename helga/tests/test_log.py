import datetime
import re

import freezegun
import pytest

from mock import patch, Mock

from helga import log


@patch('helga.log.logging')
@patch('helga.log.settings')
def test_getLogger(settings, logging):
    logger = Mock()
    handler = Mock()
    formatter = Mock()

    settings.LOG_LEVEL = 'INFO'
    settings.LOG_FILE = None
    settings.LOG_FORMAT = None

    expected_format = '%(asctime)-15s [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s'

    logging.getLogger.return_value = logger
    logging.StreamHandler.return_value = handler
    logging.Formatter.return_value = formatter

    log.getLogger('foo')
    logging.getLogger.assert_called_with('foo')
    logger.setLevel.assert_called_with(logging.INFO)
    logger.addHandler.assert_called_with(handler)
    logging.Formatter.assert_called_with(expected_format)
    handler.setFormatter.assert_called_with(formatter)
    assert not logger.propagate


@patch('helga.log.logging')
@patch('helga.log.settings')
def test_get_logger_uses_log_file(settings, logging):
    logger = Mock()
    handler = Mock()
    formatter = Mock()

    settings.LOG_LEVEL = 'INFO'
    settings.LOG_FILE = '/path/to/foo.log'
    settings.LOG_FORMAT = None

    logging.getLogger.return_value = logger
    logging.StreamHandler.return_value = handler
    logging.Formatter.return_value = formatter

    log.getLogger('foo')
    logging.handlers.RotatingFileHandler.assert_called_with(filename=settings.LOG_FILE,
                                                            maxBytes=50*1024*1024,
                                                            backupCount=6)


@patch('helga.log.logging')
@patch('helga.log.settings')
def test_get_logger_uses_custom_formatter(settings, logging):
    logger = Mock()
    handler = Mock()
    formatter = Mock()

    settings.LOG_LEVEL = 'INFO'
    settings.LOG_FILE = '/path/to/foo.log'
    settings.LOG_FORMAT = 'blah blah blah'

    logging.getLogger.return_value = logger
    logging.StreamHandler.return_value = handler
    logging.Formatter.return_value = formatter

    log.getLogger('foo')
    logging.Formatter.assert_called_with(settings.LOG_FORMAT)


@patch('helga.log.os')
@patch('helga.log.logging')
@patch('helga.log.settings')
def test_get_channel_logger(settings, logging, os):
    logger = Mock()
    handler = Mock()
    formatter = Mock()

    def os_join(*args):
        return '/'.join(args)

    settings.CHANNEL_LOGGING_DIR = '/path/to/channels'
    settings.CHANNEL_LOGGING_DB = False
    os.path.exists.return_value = True
    os.path.join = os_join

    # Mocked returns
    logging.getLogger.return_value = logger
    logging.Formatter.return_value = formatter

    with patch.object(log, 'ChannelLogFileHandler'):
        log.ChannelLogFileHandler.return_value = handler
        log.get_channel_logger('#foo')

        # Gets the right logger
        logging.getLogger.assert_called_with('channel_logger/#foo')
        logger.setLevel.assert_called_with(logging.INFO)
        assert logger.propagate is False

        # Sets the handler correctly
        log.ChannelLogFileHandler.assert_called_with('/path/to/channels/#foo')
        handler.setFormatter.assert_called_with(formatter)

        # Sets the formatter correctly
        logging.Formatter.assert_called_with('%(utctime)s - %(nick)s - %(message)s')

        # Logger uses the handler
        logger.addHandler.assert_called_with(handler)


@patch('helga.log.os')
@patch('helga.log.logging')
@patch('helga.log.settings')
def test_get_channel_logger_creates_log_dirs(settings, logging, os):
    def os_join(*args):
        return '/'.join(args)

    settings.CHANNEL_LOGGING_DIR = '/path/to/channels'
    settings.CHANNEL_LOGGING_DB = False
    os.path.exists.return_value = False
    os.path.join = os_join

    log.get_channel_logger('#foo')

    os.makedirs.assert_called_with('/path/to/channels/#foo')


class TestChannelLogFileHandler(object):

    def setup(self):
        self.handler = log.ChannelLogFileHandler('/tmp')

    def test_setup_correctly(self):
        assert self.handler.basedir == '/tmp'
        assert re.match(r'/tmp/[0-9]{4}-[0-9]{2}-[0-9]{2}.txt',
                        self.handler.baseFilename)

    def test_compute_next_rollover(self):
        expected = datetime.datetime(2014, 11, 1)
        with freezegun.freeze_time('2014-10-31 08:15'):
            assert self.handler.compute_next_rollover() == expected

    @freezegun.freeze_time('2014-10-31 08:15')
    def test_current_filename(self):
        assert self.handler.current_filename() == '2014-10-31.txt'

    @pytest.mark.parametrize('datestr,rollover', [
        ('2014-10-31 08:15', False),
        ('2014-11-01 00:00', True),
        ('2014-11-01 08:15', True),
    ])
    def test_shouldRollover(self, datestr, rollover):
        self.handler.next_rollover = datetime.datetime(2014, 11, 1)
        with freezegun.freeze_time(datestr):
            assert self.handler.shouldRollover(None) is rollover

    def test_do_rollover(self):
        stream = Mock()
        self.handler.stream = stream

        old_rollover = self.handler.next_rollover
        old_filename = self.handler.baseFilename
        expected_rollover = datetime.datetime(2014, 11, 1, 0, 0, 0)

        assert old_rollover != expected_rollover

        with freezegun.freeze_time('2014-10-31 08:15'):
            with patch.object(self.handler, '_open'):
                self.handler.doRollover()
                assert stream.close.called
                assert self.handler._open.called
                assert self.handler.baseFilename != old_filename
                assert self.handler.baseFilename == '/tmp/2014-10-31.txt'
                assert self.handler.next_rollover == expected_rollover


def test_utc_time_filter():
    record = Mock()
    filter = log.UTCTimeLogFilter()
    date = datetime.datetime(2014, 10, 31, 8, 15)
    with freezegun.freeze_time(date):
        filter.filter(record)
        assert record.utcnow == date
        assert record.utctime == '08:15:00'
