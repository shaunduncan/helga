# -*- coding: utf8 -*-
import re

from mock import Mock, call, patch
from unittest import TestCase

from helga.comm import xmpp


class FactoryTestCase(TestCase):

    def setUp(self):
        server = {
            'HOST': 'example.com',
            'USERNAME': 'user',
            'PASSWORD': 'password',
        }

        with patch.object(xmpp.settings, 'SERVER', server):
            self.factory = xmpp.Factory()

    def test_default_settings(self):
        assert self.factory.jid.full() == 'user@example.com'
        assert self.factory.auth.password == 'password'
        assert isinstance(self.factory.client, xmpp.Client)
        assert self.factory.protocol == xmpp.xmlstream.XmlStream

    def test_using_custom_jid(self):
        server = {
            'JID': 'me@somehost.net',
            'HOST': 'example.com',
            'USERNAME': 'foobar',
            'PASSWORD': 'hunter2',
        }

        with patch.object(xmpp.settings, 'SERVER', server):
            factory = xmpp.Factory()
            assert factory.jid.full() == 'me@somehost.net'
            assert factory.auth.password == 'hunter2'

    @patch('helga.comm.xmpp.settings')
    @patch('helga.comm.xmpp.reactor')
    def test_client_connection_lost_retries(self, reactor, settings):
        settings.AUTO_RECONNECT = True
        settings.AUTO_RECONNECT_DELAY = 1
        connector = Mock()
        self.factory.clientConnectionLost(connector, Exception)
        reactor.callLater.assert_called_with(1, connector.connect)

    @patch('helga.comm.xmpp.settings')
    def test_client_connection_lost_raises(self, settings):
        settings.AUTO_RECONNECT = False
        connector = Mock()
        self.assertRaises(Exception, self.factory.clientConnectionLost, connector, Exception)

    @patch('helga.comm.xmpp.settings')
    @patch('helga.comm.xmpp.reactor')
    def test_client_connection_failed(self, reactor, settings):
        settings.AUTO_RECONNECT = False
        self.factory.clientConnectionFailed(Mock(), reactor)
        assert reactor.stop.called

    @patch('helga.comm.xmpp.settings')
    @patch('helga.comm.xmpp.reactor')
    def test_client_connection_failed_retries(self, reactor, settings):
        settings.AUTO_RECONNECT = True
        settings.AUTO_RECONNECT_DELAY = 1
        connector = Mock()
        self.factory.clientConnectionFailed(connector, reactor)
        reactor.callLater.assert_called_with(1, connector.connect)


class ClientTestCase(TestCase):

    def setUp(self):
        settings = {
            'NICK': 'helga',
            'SERVER': {
                'HOST': 'example.com',
                'USERNAME': 'user',
                'PASSWORD': 'password',
            },
        }

        with patch.multiple(xmpp.settings, **settings):
            self.factory = xmpp.Factory()
            self.client = xmpp.Client(self.factory)

    def _dict_mock(self, **kwargs):
        """
        Get a mock that allows __getitem__
        """
        item = Mock()
        item.data = kwargs
        item.__getitem__ = lambda s, k: s.data[k]
        return item

    def test_default_settings(self):
        assert self.client.factory == self.factory
        assert self.client.jid == self.factory.jid
        assert self.client.nickname == 'helga'
        assert self.client.stream is None
        assert self.client.conference_host == 'conference.example.com'
        assert self.client.channels == set()
        assert self.client.last_message == {}
        assert self.client.channel_loggers == {}
        assert self.client._heartbeat is None

    def test_uses_custom_muc_host(self):
        with patch.object(xmpp.settings, 'SERVER', {'MUC_HOST': 'my.host.com'}):
            client = xmpp.Client(Mock())
            assert client.conference_host == 'my.host.com'

    def test_factory_bootstrapped(self):
        factory = Mock()

        with patch.object(xmpp.settings, 'SERVER', {'MUC_HOST': 'my.host.com'}):
            client = xmpp.Client(factory)

            factory.addBootstrap.assert_has_calls([
                call(xmpp.xmlstream.STREAM_CONNECTED_EVENT, client.on_connect),
                call(xmpp.xmlstream.STREAM_END_EVENT, client.on_disconnect),
                call(xmpp.xmlstream.STREAM_AUTHD_EVENT, client.on_authenticated),
                call(xmpp.xmlstream.INIT_FAILED_EVENT, client.on_init_failed),
                call('/message[@type="chat" or @type="groupchat"]', client.on_message),
                call('/presence[@type="unavailable"]', client.on_user_left),
                call('/presence/x/item[@role!="none"]', client.on_user_joined),
                call('/presence[@type="subscribe"]', client.on_subscribe),
                call('/message/x', client.on_invite),
                call('/presence/error/conflict', client.on_nick_collision),
                call('/iq/ping', client.on_ping),
            ])

    @patch('helga.comm.xmpp.task')
    def test_start_heartbeat(self, task):
        task.LoopingCall.return_value = task

        with patch.object(self.client, '_stop_heartbeat'):
            self.client._start_heartbeat()
            assert self.client._heartbeat == task
            self.client._heartbeat.start.assert_called_with(60, now=False)

    @patch('helga.comm.xmpp.logger')
    def test_stop_heartbeat_no_active_heartbeat(self, logger):
        with patch.object(self.client, '_heartbeat', None):
            self.client._stop_heartbeat()
            assert not logger.info.called

    def test_stop_heartbeat(self):
        heartbeat = Mock()
        with patch.object(self.client, '_heartbeat', heartbeat):
            self.client._stop_heartbeat()
            assert self.client._heartbeat is None
            assert heartbeat.stop.called

    @patch('helga.comm.xmpp.uuid')
    def test_ping(self, uuid):
        uuid.uuid4.return_value = 'UUID'

        expected = xmpp.domish.Element(('', 'iq'), attribs={
            'id': 'UUID',
            'from': self.client.jid.full(),
            'to': xmpp.settings.SERVER['HOST'],
            'type': 'get',
        })
        expected.addElement('ping', 'urn:xmpp:ping')

        with patch.object(self.client, 'stream'):
            self.client.ping()
            output = self.client.stream.send.call_args[0][0].toXml()
            assert output == expected.toXml()

            # Either single or double quotes
            assert ('<ping xmlns="urn:xmpp:ping"' in output or
                    "<ping xmlns='urn:xmpp:ping'" in output)

    def test_on_ping(self):
        ping = self._dict_mock(**{
            'to': 'helga@example.com',
            'from': 'example.com',
            'type': 'get',
            'id': 'unique-ping-id',
        })

        expected = xmpp.domish.Element(('', 'iq'), attribs={
            'id': 'unique-ping-id',
            'to': 'example.com',
            'from': 'helga@example.com',
            'type': 'result',
        })

        with patch.object(self.client, 'stream'):
            self.client.on_ping(ping)
            assert self.client.stream.send.call_args[0][0].toXml() == expected.toXml()

    def test_on_connect(self):
        stream = Mock()
        self.client.on_connect(stream)
        assert self.client.stream == stream

    def test_on_connect_starts_heartbeat(self):
        with patch.object(self.client, '_start_heartbeat'):
            self.client.on_connect(Mock())
            assert self.client._start_heartbeat.called

    def test_on_disconnect(self):
        with patch.object(self.client, '_stop_heartbeat'):
            self.client.on_disconnect(Mock())
            assert self.client._stop_heartbeat.called

    def test_set_presence(self):
        self.client.stream = Mock()
        self.client.set_presence('online')
        element = self.client.stream.send.call_args[0][0]
        assert element.toXml() == '<presence><status>online</status></presence>'

    def test_on_authenticated_sets_online_presence(self):
        with patch.object(self.client, 'set_presence'):
            with patch.object(xmpp.settings, 'CHANNELS', []):
                self.client.on_authenticated(Mock())
                self.client.set_presence.assert_called_with('Online')

    def test_on_authenticated_auto_joins_channels(self):
        channels = [('#bots',), ('#all',)]

        with patch.multiple(self.client, set_presence=Mock(), join=Mock()):
            with patch.object(xmpp.settings, 'CHANNELS', channels):
                self.client.on_authenticated(Mock())
                self.client.join.assert_has_calls([call('#bots'), call('#all')])

    def test_on_authenticated_auto_joins_channels_as_strings(self):
        channels = ['#bots', '#all']

        with patch.multiple(self.client, set_presence=Mock(), join=Mock()):
            with patch.object(xmpp.settings, 'CHANNELS', channels):
                self.client.on_authenticated(Mock())
                self.client.join.assert_has_calls([call('#bots'), call('#all')])

    @patch('helga.comm.xmpp.smokesignal')
    def test_on_authenticated_emits_signal(self, smokesignal):
        with patch.multiple(self.client, set_presence=Mock(), join=Mock()):
            with patch.object(xmpp.settings, 'CHANNELS', []):
                self.client.on_authenticated(Mock())
                smokesignal.emit.assert_called_with('signon', self.client)

    def test_on_init_failed(self):
        self.client.stream = Mock()
        self.client.on_init_failed(Mock())
        assert self.client.stream.sendFooter.called

    @patch('helga.comm.xmpp.log')
    def test_get_channel_logger_no_existing_logger(self, log):
        self.client.channel_loggers = {}
        log.get_channel_logger.return_value = 'foo'

        assert 'foo' == self.client.get_channel_logger('#foo')
        assert '#foo' in self.client.channel_loggers

    @patch('helga.comm.xmpp.log')
    def test_get_channel_logger_existing_logger(self, log):
        self.client.channel_loggers = {'#foo': 'bar'}
        log.get_channel_logger.return_value = 'foo'

        assert 'bar' == self.client.get_channel_logger('#foo')
        assert not log.get_channel_logger.called

    @patch('helga.comm.xmpp.settings')
    def test_log_channel_message(self, settings):
        settings.CHANNEL_LOGGING = True
        logger = Mock()

        with patch.object(self.client, 'get_channel_logger'):
            self.client.get_channel_logger.return_value = logger
            self.client.log_channel_message('foo', 'bar', 'baz')
            self.client.get_channel_logger.assert_called_with('foo')
            logger.info.assert_called_with('baz', extra={'nick': 'bar'})

    @patch('helga.comm.xmpp.smokesignal')
    def test_joined(self, signal):
        # Test str and unicode
        for channel in ('foo', u'☃'):
            assert channel not in self.client.channels
            self.client.joined(channel)
            assert channel in self.client.channels
            signal.emit.assert_called_with('join', self.client, channel)

    @patch('helga.comm.xmpp.smokesignal')
    def test_left(self, signal):
        # Test str and unicode
        for channel in ('foo', u'☃'):
            self.client.channels.add(channel)
            self.client.left(channel)
            assert channel not in self.client.channels
            signal.emit.assert_called_with('left', self.client, channel)

    def test_parse_nick_groupchat(self):
        message = self._dict_mock(**{'from': 'room@conference.example.com/nick'})
        assert self.client.parse_nick(message) == 'nick'

    def test_parse_nick_chat(self):
        message = self._dict_mock(**{'from': 'nick@example.com/resource'})
        assert self.client.parse_nick(message) == 'nick'

    def test_parse_channel_groupchat(self):
        message = self._dict_mock(**{
            'from': 'room@conference.example.com/nick',
            'type': 'groupchat',
        })

        assert self.client.parse_channel(message) == '#room'

    def test_parse_channel_groupchat_privmsg(self):
        message = self._dict_mock(**{
            'from': 'room@conference.example.com/nick',
            'type': 'chat',
        })

        assert self.client.parse_channel(message) == 'nick'

    def test_parse_channel_privmsg(self):
        message = self._dict_mock(**{
            'from': 'nick@example.com/resource',
            'type': 'chat',
        })

        assert self.client.parse_channel(message) == 'nick'

    def test_parse_channel_no_type_is_privmsg(self):
        message = self._dict_mock(**{'from': 'nick@example.com/resource'})
        assert self.client.parse_channel(message) == 'nick'

    def test_parse_channel_presence(self):
        message = self._dict_mock(**{'from': 'room@example.com/nick'})
        message.name = 'presence'
        assert self.client.parse_channel(message) == '#room'

    def test_parse_message_ignores_delayed(self):
        element = xmpp.domish.Element((None, 'message'))
        element.addElement('delay')
        assert self.client.parse_message(element) == ''

    def test_parse_message(self):
        element = xmpp.domish.Element((None, 'message'))
        element.addElement('body', content='message body')
        assert self.client.parse_message(element) == 'message body'

    def test_parse_message_unicode(self):
        snowman = u'☃'
        element = xmpp.domish.Element((None, 'message'))
        element.addElement('body', content=snowman)
        assert self.client.parse_message(element) == snowman

    def test_is_public_channel(self):
        assert self.client.is_public_channel('#foo')
        assert not self.client.is_public_channel('foo')

    @patch('helga.comm.xmpp.registry')
    def test_on_message_empty_message(self, registry):
        element = xmpp.domish.Element((None, 'message'))
        element.attributes = {
            'from': 'bots@conference.example.com/nick',
            'type': 'groupchat',
        }
        element.addElement('body', content='')

        with patch.object(self.client, 'msg'):
            self.client.on_message(element)
            assert not registry.process.called

    @patch('helga.comm.xmpp.registry')
    def test_on_message_from_self(self, registry):
        element = xmpp.domish.Element((None, 'message'))
        element.attributes = {
            'from': 'bots@conference.example.com/helga',
            'type': 'groupchat',
        }
        element.addElement('body', content='message body')

        with patch.multiple(self.client, nickname='helga', msg=Mock()):
            self.client.on_message(element)
            assert not registry.process.called

    @patch('helga.comm.xmpp.registry')
    def test_on_message_sends_single_string(self, registry):
        element = xmpp.domish.Element((None, 'message'))
        element.attributes = {
            'from': 'bots@conference.example.com/nick',
            'type': 'groupchat',
        }
        element.addElement('body', content='message body')
        registry.process.return_value = ['line1', 'line2']

        with patch.object(self.client, 'msg'):
            self.client.on_message(element)
            self.client.msg.assert_called_with('#bots', 'line1\nline2')

    @patch('helga.comm.xmpp.registry')
    def test_on_message_responds_to_user_when_private(self, registry):
        element = xmpp.domish.Element((None, 'message'))
        element.attributes = {
            'from': 'nick@example.com',
            'type': 'chat',
        }
        element.addElement('body', content='message body')
        registry.process.return_value = ['line1', 'line2']

        with patch.multiple(self.client, nickname='helga', msg=Mock()):
            self.client.on_message(element)
            self.client.msg.assert_called_with('nick', 'line1\nline2')

    @patch('helga.comm.xmpp.registry')
    def test_on_message_logs_public_channel_message(self, registry):
        element = xmpp.domish.Element((None, 'message'))
        element.attributes = {
            'from': 'bots@conference.example.com/nick',
            'type': 'groupchat',
        }
        element.addElement('body', content='message body')
        registry.process.return_value = ['line1', 'line2']

        with patch.multiple(self.client, log_channel_message=Mock(), msg=Mock(), nickname='helga'):
            self.client.on_message(element)
            self.client.log_channel_message.assert_has_calls([
                call('#bots', 'nick', 'message body'),
                call('#bots', 'helga', 'line1\nline2'),
            ])

    def test_msg_public_message(self):
        self.client.stream = Mock()
        expected = xmpp.domish.Element(('jabber:client', 'message'))
        expected.attributes = {
            'to': 'bots@conference.example.com',
            'from': self.client.jid.full(),
            'type': 'groupchat',
        }
        expected.addElement('body', content='hello')

        self.client.msg('#bots', 'hello')

        assert self.client.stream.send.call_args[0][0].toXml() == expected.toXml()

    def test_msg_private_message(self):
        self.client.stream = Mock()
        expected = xmpp.domish.Element(('jabber:client', 'message'))
        expected.attributes = {
            'to': 'nick@example.com',
            'from': self.client.jid.full(),
            'type': 'chat',
        }
        expected.addElement('body', content='hello')

        self.client.msg('nick', 'hello')

        assert self.client.stream.send.call_args[0][0].toXml() == expected.toXml()

    def test_msg_sends_unicode(self):
        snowman = u'☃'

        self.client.stream = Mock()
        expected = xmpp.domish.Element(('jabber:client', 'message'))
        expected.attributes = {
            'to': 'bots@conference.example.com',
            'from': self.client.jid.full(),
            'type': 'groupchat',
        }
        expected.addElement('body', content=snowman)

        self.client.msg('#bots', snowman)

        assert self.client.stream.send.call_args[0][0].toXml() == expected.toXml()

    def test_me(self):
        with patch.object(self.client, 'msg'):
            self.client.me('#bots', 'waves')
            self.client.msg.assert_called_with('#bots', '/me waves')

    def test_me_converts_from_unicode(self):
        snowman = u'☃'
        expected = '/me \xe2\x98\x83'
        with patch.object(self.client, 'msg'):
            self.client.me('#bots', snowman)
            self.client.msg.assert_called_with('#bots', expected)

    def test_on_nick_collision(self):
        element = self._dict_mock(**{'from': 'room@conference.example.com'})
        with patch.object(self.client, 'join'):
            self.client.on_nick_collision(element)

            assert re.match(r'^helga_[\d]+$', self.client.nickname)
            self.client.join.assert_called_with('room@conference.example.com')

        # Should take the first part up to '_'
        with patch.multiple(self.client, nickname='foo_bar', join=Mock()):
            self.client.on_nick_collision(element)

            assert re.match(r'^foo_[\d]+$', self.client.nickname)
            self.client.join.assert_called_with('room@conference.example.com')

    def test_on_invite_direct(self):
        element = xmpp.domish.Element(('', 'message'))
        x = xmpp.domish.Element(('jabber:x:conference', 'x'), attribs={
            'jid': 'room@conf.example.com'
        })
        element.addChild(x)

        with patch.object(self.client, 'join'):
            self.client.on_invite(element)
            self.client.join.assert_called_with('room@conf.example.com', password='')

    def test_on_invite_ignores_probably_not_invite(self):
        element = xmpp.domish.Element(('', 'message'))
        x = xmpp.domish.Element(('', 'x'), attribs={
            'jid': 'room@conf.example.com'
        })
        element.addChild(x)

        with patch.object(self.client, 'join'):
            self.client.on_invite(element)
            assert not self.client.join.called

    def test_on_invite_direct_with_channel_password(self):
        element = xmpp.domish.Element(('', 'message'))
        x = xmpp.domish.Element(('jabber:x:conference', 'x'), attribs={
            'jid': 'room@conf.example.com',
            'password': 'foobar',
        })
        element.addChild(x)

        with patch.object(self.client, 'join'):
            self.client.on_invite(element)
            self.client.join.assert_called_with('room@conf.example.com', password='foobar')

    def test_on_invite_mediated_from_user(self):
        element = xmpp.domish.Element(('', 'message'), attribs={
            'from': 'nick@example.com',
            'to': 'room@conference.example.com',
        })
        x = xmpp.domish.Element(('', 'x'))
        x.addElement('invite')
        element.addChild(x)

        with patch.object(self.client, 'join'):
            self.client.on_invite(element)
            self.client.join.assert_called_with('room@conference.example.com', password='')

    def test_on_invite_mediated_from_room(self):
        element = xmpp.domish.Element(('', 'message'), attribs={
            'from': 'room@conference.example.com',
            'to': 'helga@example.com',
        })
        x = xmpp.domish.Element(('', 'x'))
        x.addElement('invite')
        element.addChild(x)

        with patch.object(self.client, 'join'):
            self.client.on_invite(element)
            self.client.join.assert_called_with('room@conference.example.com', password='')

    def test_on_invite_mediated_with_channel_password(self):
        element = xmpp.domish.Element(('', 'message'), attribs={
            'from': 'nick@example.com',
            'to': 'room@conference.example.com',
        })
        x = xmpp.domish.Element(('', 'x'))
        x.addElement('invite')
        x.addElement('password', content='foobar')
        element.addChild(x)

        with patch.object(self.client, 'join'):
            self.client.on_invite(element)
            self.client.join.assert_called_with('room@conference.example.com', password='foobar')

    def test_on_subscribe(self):
        element = self._dict_mock(**{'from': 'nick@example.com'})
        expected = xmpp.domish.Element(('jabber:client', 'presence'), attribs={
            'to': 'nick@example.com',
            'from': self.client.jid.full(),
            'type': 'subscribed',
        })

        with patch.object(self.client, 'stream'):
            self.client.on_subscribe(element)
            assert self.client.stream.send.call_args[0][0].toXml() == expected.toXml()

    @patch('helga.comm.xmpp.smokesignal')
    def test_on_user_joined(self, smokesignal):
        parse_nick = Mock(return_value='foo')
        parse_channel = Mock(return_value='bar')
        with patch.multiple(self.client, parse_nick=parse_nick, parse_channel=parse_channel):
            self.client.on_user_joined(Mock())
            smokesignal.emit.assert_called_with('user_joined', self.client, 'foo', 'bar')

    @patch('helga.comm.xmpp.smokesignal')
    def test_on_user_left(self, smokesignal):
        parse_nick = Mock(return_value='foo')
        parse_channel = Mock(return_value='bar')
        with patch.multiple(self.client, parse_nick=parse_nick, parse_channel=parse_channel):
            self.client.on_user_left(Mock())
            smokesignal.emit.assert_called_with('user_left', self.client, 'foo', 'bar')

    def test_join(self):
        expected = xmpp.domish.Element(('jabber:client', 'presence'), attribs={
            'to': 'bots@conf.example.com/{0}'.format(self.client.nickname),
            'from': self.client.jid.full(),
        })
        muc = xmpp.domish.Element(('http://jabber.org/protocol/muc', 'x'))
        hist = xmpp.domish.Element(('', 'history'), attribs={
            'maxchars': '0',
            'maxstanzas': '0',
        })
        muc.addChild(hist)
        expected.addChild(muc)

        with patch.multiple(self.client, stream=Mock(), joined=Mock()):
            self.client.join('bots@conf.example.com')
            assert self.client.stream.send.call_args[0][0].toXml() == expected.toXml()
            assert self.client.joined.called

    def test_join_with_simple_room_name(self):
        expected = xmpp.domish.Element(('jabber:client', 'presence'), attribs={
            'to': 'bots@{0}/{1}'.format(self.client.conference_host, self.client.nickname),
            'from': self.client.jid.full(),
        })
        muc = xmpp.domish.Element(('http://jabber.org/protocol/muc', 'x'))
        hist = xmpp.domish.Element(('', 'history'), attribs={
            'maxchars': '0',
            'maxstanzas': '0',
        })
        muc.addChild(hist)
        expected.addChild(muc)

        with patch.multiple(self.client, stream=Mock(), joined=Mock()):
            self.client.join('#bots')
            assert self.client.stream.send.call_args[0][0].toXml() == expected.toXml()
            assert self.client.joined.called

    def test_join_with_password(self):
        expected = xmpp.domish.Element(('jabber:client', 'presence'), attribs={
            'to': 'bots@conf.example.com/{0}'.format(self.client.nickname),
            'from': self.client.jid.full(),
        })
        muc = xmpp.domish.Element(('http://jabber.org/protocol/muc', 'x'))
        hist = xmpp.domish.Element(('', 'history'), attribs={
            'maxchars': '0',
            'maxstanzas': '0',
        })
        muc.addChild(hist)
        muc.addElement('password', content='foobar')
        expected.addChild(muc)

        with patch.multiple(self.client, stream=Mock(), joined=Mock()):
            self.client.join('bots@conf.example.com', 'foobar')
            assert self.client.stream.send.call_args[0][0].toXml() == expected.toXml()
            assert self.client.joined.called

    def test_leave(self):
        expected = xmpp.domish.Element(('jabber:client', 'presence'), attribs={
            'to': 'bots@conf.example.com',
            'from': self.client.jid.full(),
            'type': 'unavailable',
        })

        with patch.multiple(self.client, stream=Mock(), left=Mock()):
            self.client.leave('bots@conf.example.com')
            assert self.client.stream.send.call_args[0][0].toXml() == expected.toXml()
            assert self.client.left.called

    def test_leave_with_simple_room_name(self):
        expected = xmpp.domish.Element(('jabber:client', 'presence'), attribs={
            'to': 'bots@{0}'.format(self.client.conference_host),
            'from': self.client.jid.full(),
            'type': 'unavailable',
        })

        with patch.multiple(self.client, stream=Mock(), left=Mock()):
            self.client.leave('#bots')
            assert self.client.stream.send.call_args[0][0].toXml() == expected.toXml()
            assert self.client.left.called

    def test_format_channel_with_simple_chan(self):
        expected = 'bots@{0}'.format(self.client.conference_host)
        assert self.client.format_channel('#bots') == expected

    def test_format_channel_with_full_jid(self):
        expected = 'bots@conf.example.com'
        assert self.client.format_channel(expected) == expected

    def test_format_channel_fallback_on_jid_parse_error(self):
        expected = 'bots@{0}'.format(self.client.conference_host)

        with patch.object(xmpp.jid, 'JID', side_effect=xmpp.jid.InvalidFormat):
            assert self.client.format_channel('bots') == expected
