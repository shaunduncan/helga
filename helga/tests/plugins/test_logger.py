import time

from datetime import datetime

import pytest

from mock import patch, MagicMock

from helga.plugins import logger


@pytest.fixture(scope='function')
def settings(monkeypatch, request):
    from helga import settings as _settings

    mocked = MagicMock(spec=_settings)
    mocked.CHANNEL_LOGGING_DB = True

    monkeypatch.setattr(logger, 'settings', mocked)

    return mocked


def gen_logger_params():
    # Return a list of a message string, and expected call kwargs
    return [
        ('search foo', {'channel': '#bots', 'term': 'foo', 'nick': None}),
        ('search foo on #bar', {'channel': '#bar', 'term': 'foo', 'nick': None}),
        ('search_by me foo', {'channel': '#bots', 'term': 'foo', 'nick': 'me'}),
        ('search_by me foo on #bar', {'channel': '#bar', 'term': 'foo', 'nick': 'me'}),
        ('recent', {'channel': '#bots', 'term': None, 'nick': None}),
        ('recent on #bar', {'channel': '#bar', 'term': None, 'nick': None}),
        ('recent_by me', {'channel': '#bots', 'term': None, 'nick': 'me'}),
        ('recent_by me on #bar', {'channel': '#bar', 'term': None, 'nick': 'me'}),
    ]


def gen_do_search_params():
    # Return a list of channel, term, and nick
    return [
        ('#bots', None, None),
        ('#bots', 'foo', None),
        ('#bots', None, 'me'),
        ('#bots', 'foo', 'me'),
    ]


def test_logger_only_for_enabled_db_logging(settings):
    settings.CHANNEL_LOGGING_DB = False
    ret = logger.logger('', '', '', '', '', '')
    assert ret == 'Log searching is only available with CHANNEL_LOGGING_DB enabled'


def test_logger_ignores_invalid_subcmd(settings):
    with patch.object(logger, '_do_search'):
        assert logger.logger('', '', '', '', '', ['foo']) is None
        assert not logger._do_search.called


@pytest.mark.parametrize('message,expected', gen_logger_params())
def test_logger(message, expected, settings):
    args = message.split()
    with patch.object(logger, '_do_search'):
        logger.logger(MagicMock(), '#bots', 'me', message, 'logs', args)
        logger._do_search.assert_called_with(**expected)


@patch('helga.plugins.logger.db')
def test_do_search_no_results(db):
    qs = MagicMock()
    qs.count.return_value = 0
    db.channel_logs.find.return_value = qs
    assert ['No results found'] == list(logger._do_search('#bots'))


@pytest.mark.parametrize('channel,term,nick', gen_do_search_params())
def test_do_search(channel, term, nick, settings, monkeypatch):
    db = MagicMock()
    re = MagicMock()
    re.compile.return_value = re

    monkeypatch.setattr(logger, 'db', db)
    monkeypatch.setattr(logger, 're', re)

    settings.CHANNEL_LOGGING_DB_SEARCH_LIMIT = 10
    qs = MagicMock()
    qs.__iter__.return_value = [
        # pymongo results will be returned in descending order, which we reverse
        {
            'created': time.mktime(datetime(2002, 12, 1, 8, 15).timetuple()),
            'channel': '#bots',
            'nick': 'me',
            'message': 'from 2002',
        },
        {
            'created': time.mktime(datetime(2001, 12, 1, 8, 15).timetuple()),
            'channel': '#bots',
            'nick': 'me',
            'message': 'from 2001',
        },
    ]
    db.channel_logs.find.return_value = qs
    retval = list(logger._do_search(channel, term=term, nick=nick))

    assert retval == [
        '[12/01/2001 08:15 UTC][#bots] me - from 2001',
        '[12/01/2002 08:15 UTC][#bots] me - from 2002',
    ]

    # Assert searched correctly
    search_spec = {'$and': [{'channel': channel}]}
    if term is not None:
        search_spec['$and'].append({'message': {'$regex': re.compile(term, re.I)}})
    if nick is not None:
        search_spec['$and'].append({'nick': {'$regex': re.compile(term, re.I)}})

    db.channel_logs.find.assert_called_with(
        search_spec,
        limit=10,
        sort=[('created', logger.pymongo.DESCENDING)],
    )
