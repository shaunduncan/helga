# -*- coding: utf8 -*-
import types

from mock import Mock
from unittest import TestCase

from helga import settings
from helga.webhooks.announcements import announce


class AnnouncementTestCase(TestCase):

    def setUp(self):
        self.client = Mock()
        self.request = Mock(args={})

        def _set_response_code(self, code):
            self.response_code = code

        self.request.setResponseCode = types.MethodType(_set_response_code, self.request)

        # Ensure requests are always authenticated
        self.request.getUser.return_value = 'user'
        self.request.getPassword.return_value = 'password'
        settings.WEBHOOKS_CREDENTIALS = [('user', 'password')]

    def test_requires_message_content(self):
        assert 'Param message is required' == announce(self.request, self.client, '#foo')
        assert self.request.response_code == 400

    def test_formatted_channel(self):
        self.request.args['message'] = ['bar']
        assert 'Message Sent' == announce(self.request, self.client, 'foo')
        self.client.msg.assert_called_with('#foo', 'bar')

    def test_handles_unicode(self):
        snowman = u'☃'
        self.request.args['message'] = [snowman]
        assert 'Message Sent' == announce(self.request, self.client, '#foo')
        self.client.msg.assert_called_with('#foo', snowman)

    def test_announce(self):
        self.request.args['message'] = ['bar']
        assert 'Message Sent' == announce(self.request, self.client, '#foo')
        self.client.msg.assert_called_with('#foo', 'bar')
