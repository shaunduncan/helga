# -*- coding: utf8 -*-

import pytest

from mock import patch

from helga.comm import slack


@pytest.fixture(scope='module', autouse=True)
def patch_api():
    with patch.object(slack, 'api', return_value=None):
        yield


@pytest.fixture
def client():
    c = None

    with patch.object(slack, 'task'):
        c = slack.Client({
            'self': {
                'name': 'helga',
            },
        })

    yield c


class TestClient(object):

    def test_parse_message_simple(self, client):
        message = '<@U1234ABC> Hi'

        with patch.object(client, '_get_user_name', return_value='adeza') as mock_get_user:
            result = client._parse_incoming_message(message)
            assert '@adeza Hi' == result
            mock_get_user.assert_called_with('U1234ABC')

    def test_parse_message_complex(self, client):
        message = '<@U1234ABC|alfredo> Hi'

        with patch.object(client, '_get_user_name', return_value='alfredo') as mock_get_user:
            result = client._parse_incoming_message(message)
            assert '@alfredo Hi' == result
            mock_get_user.assert_called_with('U1234ABC')

    def test_parse_message_unescape(self, client):
        message = '<@U1234ABC> test &lt;reply&gt; &amp; more'

        with patch.object(client, '_get_user_name', return_value='alfredo') as mock_get_user:
            result = client._parse_incoming_message(message)
            assert '@alfredo test <reply> & more' == result
            mock_get_user.assert_called_with('U1234ABC')

