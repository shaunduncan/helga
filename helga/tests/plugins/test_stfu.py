# -*- coding: utf8 -*-
from mock import patch, Mock
from pretend import stub

from helga.plugins import stfu


def test_stfu_preprocess_does_nothing():
    stfu.silenced = set()
    client = stub(nickname='helga')
    chan, nick, msg = stfu.stfu(client, '#bots', 'me', 'foo')
    assert msg == 'foo'


def test_stfu_preprocess_blanks_message_when_silenced():
    stfu.silenced = set(['#bots'])
    client = stub(nickname='helga')
    chan, nick, msg = stfu.stfu(client, '#bots', 'me', 'foo')
    assert msg == ''


def test_stfu_snark_on_private_message():
    stfu.silenced = set()
    resp = stfu.stfu(stub(nickname='helga'), 'me', 'me', 'helga stfu', 'stfu', [])
    assert resp in map(lambda x: x.format(nick='me'), stfu.snarks)


def test_stfu_silences_channel():
    stfu.silenced = set()
    resp = stfu.stfu(stub(nickname='helga'), '#bots', 'me', 'helga stfu', 'stfu', [])
    assert resp in map(lambda x: x.format(nick='me'), stfu.silence_acks)
    assert '#bots' in stfu.silenced


@patch('helga.plugins.stfu.reactor')
def test_stfu_for_some_time(reactor):
    client = stub(nickname='helga')
    stfu.stfu(client, '#bots', 'me', 'helga stfu for 30', 'stfu', ['for', '30'])
    reactor.callLater.assert_called_with(30*60, stfu.auto_unsilence, client, '#bots', 30*60)


def test_stfu_unsilences_channel():
    stfu.silenced = set(['#bots'])
    resp = stfu.stfu(stub(nickname='helga'), '#bots', 'me', 'helga speak', 'speak', [])
    assert resp in map(lambda x: x.format(nick='me'), stfu.unsilence_acks)
    assert '#bots' not in stfu.silenced


def test_stfu_speak_only_speaks_once():
    stfu.silenced = set(['#bots'])
    resp = stfu.stfu(stub(nickname='helga'), '#bots', 'me', 'helga speak', 'speak', [])
    assert resp in map(lambda x: x.format(nick='me'), stfu.unsilence_acks)

    resp = stfu.stfu(stub(nickname='helga'), '#bots', 'me', 'helga speak', 'speak', [])
    assert resp is None


def test_auto_unsilence():
    stfu.silenced = set(['#bots'])
    client = Mock()
    stfu.auto_unsilence(client, '#bots', 300)
    assert '#bots' not in stfu.silenced
    client.msg.assert_called_with('#bots', 'Speaking again after waiting 5 minutes')


def test_stfu_with_unicode():
    client = stub(nickname=u'☃')
    chan, nick, msg = stfu.stfu(client, '#bots', 'me', u'helga speak ☃')
    assert chan == '#bots'
    assert nick == 'me'
    assert msg == u'helga speak ☃'


@patch('helga.plugins.stfu.reactor')
def test_stfu_handles_invalid_args(reactor):
    client = stub(nickname='helga')
    test_args = [
        ['for'],
        ['for', 'blah'],
        ['for', None],
    ]

    for args in test_args:
        stfu.stfu(client, '#bots', 'me', 'helga stfu for 30', 'stfu', args)
        assert not reactor.callLater.called
