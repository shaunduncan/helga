from mock import patch
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
    reactor.callLater.assertCalledWith(30*60, stfu.auto_unsilence, client, '#bots', 30*60)


def test_stfu_unsilences_channel():
    stfu.silenced = set(['#bots'])
    resp = stfu.stfu(stub(nickname='helga'), '#bots', 'me', 'helga speak', 'speak', [])
    assert resp in map(lambda x: x.format(nick='me'), stfu.unsilence_acks)
    assert '#bots' not in stfu.silenced
