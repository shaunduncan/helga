import sys

from mock import Mock, patch

from helga.bin import helga


class TestRun(object):

    def test_tcp(self):
        server = {
            'HOST': 'localhost',
            'PORT': 6667,
        }

        with patch.multiple(helga, smokesignal=Mock(), _get_backend=Mock(), reactor=Mock()):
            with patch.object(helga.settings, 'SERVER', server):
                factory = Mock()
                helga._get_backend.return_value = helga._get_backend
                helga._get_backend.Factory.return_value = factory

                helga.run()

                helga.smokesignal.emit.assert_called_with('started')
                helga.reactor.connectTCP.assert_called_with('localhost', 6667, factory)
                assert helga.reactor.run.called

    def test_ssl(self):
        server = {
            'HOST': 'localhost',
            'PORT': 6667,
            'SSL': True
        }

        with patch.multiple(helga, smokesignal=Mock(), _get_backend=Mock(), reactor=Mock(), ssl=Mock()):
            with patch.object(helga.settings, 'SERVER', server):
                ssl = Mock()
                helga.ssl.ClientContextFactory.return_value = ssl

                factory = Mock()
                helga._get_backend.return_value = helga._get_backend
                helga._get_backend.Factory.return_value = factory

                helga.run()

                helga.smokesignal.emit.assert_called_with('started')
                helga.reactor.connectSSL.assert_called_with('localhost', 6667, factory, ssl)
                assert helga.reactor.run.called


class TestMain(object):

    def test_uses_settings_env_var(monkeypatch):
        sys.argv = ['helga']

        with patch.multiple(helga, run=Mock(), settings=Mock()):
            with patch.dict('os.environ', {'HELGA_SETTINGS': 'foo'}):
                helga.main()
                helga.settings.configure.assert_called_with('foo')
                assert helga.run.called

    def test_settings_arg_overrides_env_var(self):
        sys.argv = ['helga', '--settings', 'bar']

        with patch.multiple(helga, run=Mock(), settings=Mock()):
            with patch.dict('os.environ', {'HELGA_SETTINGS': 'foo'}):
                helga.main()
                helga.settings.configure.assert_called_with('bar')
                assert helga.run.called
