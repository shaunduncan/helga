# coding: utf-8
import pytest

from mock import Mock

from helga.webhooks import logger


class TestIndexView(object):

    def setup(self):
        self.view = logger.Index()

    def test_title(self):
        assert self.view.title() == 'Channel Logs'

    def test_channels(self, monkeypatch):
        monkeypatch.setattr(logger, 'os', Mock())
        logger.os.listdir.return_value = ['#foo', '#bar', '#baz']

        assert list(self.view.channels()) == ['bar', 'baz', 'foo']

    def test_channels_empty_for_no_logs(self, monkeypatch):
        monkeypatch.setattr(logger, 'os', Mock())
        logger.os.path.isdir.return_value = False
        logger.os.listdir.side_effect = OSError

        try:
            retval = list(self.view.channels())
        except:
            pytest.fail('Should not have raised an Exception')
        else:
            assert retval == []

    def test_channels_hides_blacklist(self, monkeypatch):
        monkeypatch.setattr(logger, 'os', Mock())

        # Should handle with or without leading '#'
        monkeypatch.setattr(logger, 'settings', Mock(
            CHANNEL_LOGGING_HIDE_CHANNELS=['#foo', 'bar']
        ))

        logger.os.listdir.return_value = ['#foo', '#bar', '#baz']

        assert list(self.view.channels()) == ['baz']


class TestChannelIndexView(object):

    def setup(self):
        self.view = logger.ChannelIndex('foo')

    def test_title(self):
        assert self.view.title() == '#foo Channel Logs'

    def test_dates(self, monkeypatch):
        monkeypatch.setattr(logger, 'os', Mock())
        logger.os.path.isdir.return_value = True
        logger.os.listdir.return_value = [
            '2010-12-01.txt',
            '2011-12-01.txt',
            '2012-12-01.txt',
            '2012-10-31.txt',
        ]

        assert list(self.view.dates()) == [
            '2012-12-01',
            '2012-10-31',
            '2011-12-01',
            '2010-12-01',
        ]

    def test_dates_404(self, monkeypatch):
        monkeypatch.setattr(logger, 'os', Mock())
        logger.os.path.isdir.return_value = False

        with pytest.raises(logger.HttpError):
            list(self.view.dates())


class TestChannelLogView(object):

    def setup(self):
        self.view = logger.ChannelLog('foo', '2014-12-01')

    def test_title(self):
        assert self.view.title() == '#foo Channel Logs for 2014-12-01'

    def test_messages_404(self, monkeypatch):
        monkeypatch.setattr(logger, 'os', Mock())
        logger.os.path.isfile.return_value = False

        with pytest.raises(logger.HttpError):
            list(self.view.messages())

    def test_messages(self, tmpdir):
        logger.settings.CHANNEL_LOGGING_DIR = str(tmpdir)

        # Create tmp file
        file = tmpdir.mkdir('#foo').join('2014-12-01.txt')
        file.write('\n'.join([
            '00:00:00 - foo - this is what i said',
            '12:01:35 - bar - another thing i said',
            '16:17:18 - baz - this - has - delimiters',
            u'21:22:23 - qux - ☃'.encode('utf-8')
        ]), mode='wb')

        assert list(self.view.messages()) == [
            {
                'time': '00:00:00',
                'nick': 'foo',
                'message': 'this is what i said',
            },
            {
                'time': '12:01:35',
                'nick': 'bar',
                'message': 'another thing i said',
            },
            {
                'time': '16:17:18',
                'nick': 'baz',
                'message': 'this - has - delimiters',
            },
            {
                'time': '21:22:23',
                'nick': 'qux',
                'message': u'☃',
            },
        ]

    def test_messages_with_multiline_content(self, tmpdir):
        logger.settings.CHANNEL_LOGGING_DIR = str(tmpdir)

        # Create tmp file
        file = tmpdir.mkdir('#foo').join('2014-12-01.txt')
        file.write('\n'.join([
            '00:00:00 - foo - this is what i said',
            '...and here',
            '...and here again',
            u'...☃'.encode('utf-8')
        ]), mode='wb')

        assert list(self.view.messages()) == [
            {
                'time': '00:00:00',
                'nick': 'foo',
                'message': u'this is what i said\n...and here\n...and here again\n...☃',
            }
        ]

    def test_messages_with_unhandled_content(self, tmpdir):
        logger.settings.CHANNEL_LOGGING_DIR = str(tmpdir)

        # Create tmp file
        file = tmpdir.mkdir('#foo').join('2014-12-01.txt')
        file.write("it's lonely here")

        assert list(self.view.messages()) == [
            {
                'time': '',
                'nick': '',
                'message': "it's lonely here",
            }
        ]

    def test_download(self, tmpdir):
        request = Mock()
        contents = ('00:00:00 - foo - this is what i said\n'
                    '12:01:35 - bar - another thing i said\n'
                    '16:17:18 - baz - this - has - delimiters\n'
                    u'21:22:23 - qux - ☃'.encode('utf-8'))

        logger.settings.CHANNEL_LOGGING_DIR = str(tmpdir)

        # Create tmp file
        file = tmpdir.mkdir('#foo').join('2014-12-01.txt')
        file.write(contents, mode='wb')

        assert self.view.download(request) == contents
        request.setHeader.assert_any_call('Content-Type', 'text/plain')
        request.setHeader.assert_any_call('Content-Disposition', 'attachment; filename=2014-12-01.txt')


class TestWebhook(object):

    def setup(self):
        self.request = Mock()
        logger.settings.CHANNEL_LOGGING = True

    def test_raises_501(self):
        logger.settings.CHANNEL_LOGGING = False
        with pytest.raises(logger.HttpError):
            logger.logger(None, None)

    def _mock_log_dir(self, tmpdir):
        # Create tmp file
        logger.settings.CHANNEL_LOGGING_DIR = str(tmpdir)
        file = tmpdir.mkdir('#foo').join('2014-12-01.txt')
        file.write('00:00:00 - foo - this is what i said')

    def test_renders_index(self, tmpdir):
        self._mock_log_dir(tmpdir)
        response = logger.logger(self.request, None)
        self.request.setHeader.assert_called_with('Content-Type', 'text/html')

        # Output asserts
        assert '<title>Channel Logs</title>' in response
        assert '<a href="/logger/foo">#foo</a>' in response

    def test_renders_channel_index(self, tmpdir):
        self._mock_log_dir(tmpdir)
        response = logger.logger(self.request, None, 'foo')
        self.request.setHeader.assert_called_with('Content-Type', 'text/html')

        # Output asserts
        assert '<title>#foo Channel Logs</title>' in response
        assert '<a href="/logger/foo/2014-12-01">2014-12-01</a>' in response

    def test_renders_channel_log(self, tmpdir):
        self._mock_log_dir(tmpdir)
        response = logger.logger(self.request, None, 'foo', '2014-12-01')
        self.request.setHeader.assert_called_with('Content-Type', 'text/html')

        # Output asserts
        assert '<title>#foo Channel Logs for 2014-12-01</title>' in response
        assert '<td><a href="#00:00:00" name="00:00:00">00:00:00</a></td>' in response
        assert '<td>foo</td>' in response
        assert '<td><pre>this is what i said</pre></td>' in response

    def test_renders_channel_log_as_text(self, tmpdir):
        self._mock_log_dir(tmpdir)
        response = logger.logger(self.request, None, 'foo', '2014-12-01', as_text=True)
        self.request.setHeader.assert_any_call('Content-Type', 'text/plain')
        self.request.setHeader.assert_any_call('Content-Disposition', 'attachment; filename=2014-12-01.txt')

        # Output asserts
        assert response == '00:00:00 - foo - this is what i said'
