import pytest

from mock import Mock, patch

from helga.plugins import ignore


class TestIgnore(object):

    def setup(self):
        patch.object(ignore, 'ignored', set()).start()
        patch.object(ignore.settings, 'OPERATORS', ['op']).start()

    def teardown(self):
        patch.stopall()

    @patch.multiple(ignore, _do_preprocess=Mock(), _do_command=Mock())
    def test_runs_preprocessor(self):
        ignore.ignore(Mock(), '#bots', 'me', 'foo')
        assert not ignore._do_command.called
        ignore._do_preprocess.assert_called_with('#bots', 'me', 'foo')

    @patch.multiple(ignore, _do_preprocess=Mock(), _do_command=Mock())
    def test_runs_command(self):
        ignore.ignore(Mock(), '#bots', 'me', 'foo', 'ignore', ['list'])
        assert not ignore._do_preprocess.called
        ignore._do_command.assert_called_with('me', ['list'])

    def test_preprocessor_ignores(self):
        ignore.ignored.add('me')
        chan, nick, msg = ignore._do_preprocess('#bots', 'me', 'ok')
        assert msg == ''

    def test_preprocessor_does_nothing(self):
        chan, nick, msg = ignore._do_preprocess('#bots', 'me', 'ok')
        assert msg == 'ok'

    @pytest.mark.parametrize('args', ([], ['list']))
    def test_command_list(self, args):
        ignore.ignored.add('foo')
        assert 'Ignoring: foo' == ignore._do_command('me', args)

    @pytest.mark.parametrize('args', (['add'], ['remove']))
    def test_command_add_remove_ops_only(self, args):
        resp = 'Sorry me, only operators can do that'
        assert resp == ignore._do_command('me', args)

    def test_command_add(self):
        assert 'me' not in ignore.ignored
        assert 'OK op, I will ignore me' == ignore._do_command('op', ['add', 'me'])
        assert 'me' in ignore.ignored

    def test_command_remove(self):
        ignore.ignored.add('me')
        assert 'OK op, I will stop ignoring me' == ignore._do_command('op', ['remove', 'me'])
        assert 'me' not in ignore.ignored
