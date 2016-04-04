# -*- coding: utf8 -*-

from mock import patch
import unittest

from helga.comm import slack

class ClientTestCase(unittest.TestCase):

    @patch('helga.comm.slack.settings')
    @patch('helga.comm.slack.ClientProtocol._get_self_name')
    def setUp(self, _get_self_name, settings):
        settings.SERVER = {'API_KEY': 'xoxb-asdf'}
        _get_self_name.return_value = 'helga'
        self.client = slack.ClientProtocol()

    @patch('helga.comm.slack.ClientProtocol._get_user_name')
    def test_parse_message_simple(self, _get_user_name):
        _get_user_name.return_value = 'adeza'
        message = '<@U1234ABC> Hi'
        result = self.client._parse_incoming_message(message)
        _get_user_name.assert_called_once_with('U1234ABC')
        self.assertEquals('@adeza Hi', result)

    @patch('helga.comm.slack.ClientProtocol._get_user_name')
    def test_parse_message_complex(self, _get_user_name):
        _get_user_name.return_value = 'adeza'
        message = '<@U1234ABC|alfredo> Hi'
        result = self.client._parse_incoming_message(message)
        _get_user_name.assert_called_once_with('U1234ABC')
        self.assertEquals('@adeza Hi', result)

if __name__ == '__main__':
    unittest.main()
