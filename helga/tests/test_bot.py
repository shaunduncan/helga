from mock import Mock
from unittest import TestCase

from helga import settings
from helga.bot import Helga


settings.DISABLE_AUTOBOT = True


class HelgaTestCase(TestCase):

    def setUp(self):
        self.helga = Helga(load=False)

    def test_join_channel(self):
        self.helga.join_channel('#all')

        assert '#all' in self.helga.channels

    def test_leave_channel(self):
        self.helga.join_channel('#all')
        self.helga.leave_channel('#all')

        assert '#all' not in self.helga.channels

    def test_nick(self):
        self.helga.client = Mock()
        self.helga.client.nickname = 'foo'

        assert self.helga.nick == 'foo'

    def test_nick_no_client(self):
        assert self.helga.nick == ''

    def test_get_current_nick_unknown_user(self):
        assert self.helga.get_current_nick('foo') == 'foo'

    def test_get_current_nick_is_current(self):
        self.helga.users = {'foo': ('foobar',)}

        assert self.helga.get_current_nick('foo') == 'foo'

    def test_get_current_nick_is_old_nick(self):
        self.helga.users = {'foo': ('foobar',)}

        assert self.helga.get_current_nick('foobar') == 'foo'

    def test_update_user_nick_adds_new_user(self):
        self.helga.update_user_nick(None, 'foo')

        assert self.helga.users['foo'] == set(['foo'])

    def test_update_user_nick_no_changes(self):
        user_set = {'foo': set(['foo'])}
        self.helga.users = user_set
        self.helga.update_user_nick('foo', 'foo')

        assert self.helga.users == user_set

    def test_update_user_nick_remaps(self):
        old = {'foobar': set(['foobar'])}
        new = {'foo': set(['foo', 'foobar'])}
        self.helga.users = old
        self.helga.update_user_nick('foobar', 'foo')

        assert self.helga.users == new

    def setup_process(self, preprocess_ret, process_ret):
        self.helga.extensions = Mock()
        self.helga.client = Mock()

        def set_process_ret(message):
            message.response = process_ret

        def set_preprocess_ret(message):
            message.response = preprocess_ret

        self.helga.extensions.process.return_value = set_process_ret
        self.helga.extensions.preprocess.return_value = set_preprocess_ret

    def test_process_does_nothing(self):
        msg = Mock()
        msg.has_response = False

        self.setup_process(None, None)
        self.helga.process(msg)

        assert not self.helga.client.msg.called

    def test_process_preprocess_skips_extensions(self):
        msg = Mock()
        msg.has_response = True

        self.setup_process('OK', None)
        self.helga.process(msg)

        assert not self.helga.extensions.process.called

    def test_process_runs_extensions(self):
        msg = Mock()
        msg.response = None

        self.setup_process(None, None)

        def process(m):
            m.has_response = True
            m.response = 'foo'

        self.helga.extensions.process = process

        msg.format_response.return_value = 'foo'
        msg.resp_channel = '#bots'
        msg.has_repsonse = False

        self.helga.process(msg)

        self.helga.client.msg.assertCalledWith('#bots', 'foo')
