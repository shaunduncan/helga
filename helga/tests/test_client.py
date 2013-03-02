from unittest import TestCase

from helga.client import Message


class MessageTestCase(TestCase):

    def setUp(self):
        self.message = Message('foo', '#bar', 'baz', True)

    def test_format_response_does_formatting(self):
        expected = 'foo #bar bar'
        self.message.response = '%(nick)s %(channel)s %(norm_channel)s'

        assert self.message.format_response() == expected

    def test_format_response_multiline_response(self):
        expected = 'foo\nbar\nbaz'
        self.message.response = ['foo', 'bar', 'baz']

        assert self.message.format_response() == expected

    def test_format_response_accepts_kwargs(self):
        expected = 'foo bar'
        self.message.response = 'foo %(kwarg)s'

        assert self.message.format_response(kwarg='bar') == expected
