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
