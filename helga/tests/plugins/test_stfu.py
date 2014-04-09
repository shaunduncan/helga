from mock import Mock, patch
from pretend import stub

from helga.plugins import stfu


def test_stfu_postprocess_does_nothing():
    stfu.silenced = set()
    client = stub(nickname='helga')
    assert 'response' == stfu.stfu(client, '#bots', 'me', 'foo', 'response')


def test_stfu_postprocess_blanks_response_when_silenced():
    stfu.silenced = set(['#bots'])
    client = stub(nickname='helga')
    assert stfu.stfu(client, '#bots', 'me', 'foo', 'response') is None


def test_stfu_snark_on_private_message():
    client = Mock()
    stfu.silenced = set()
    stfu.stfu(client, 'me', 'me', 'helga stfu', 'stfu', [])

    chan, resp = client.msg.call_args[0]
    assert resp in map(lambda x: x.format(nick='me'), stfu.snarks)


def test_stfu_silences_channel():
    client = Mock()
    stfu.silenced = set()
    stfu.stfu(client, '#bots', 'me', 'helga stfu', 'stfu', [])

    chan, resp = client.msg.call_args[0]
    assert resp in map(lambda x: x.format(nick='me'), stfu.silence_acks)
    assert '#bots' in stfu.silenced


@patch('helga.plugins.stfu.reactor')
def test_stfu_for_some_time(reactor):
    client = Mock()
    stfu.stfu(client, '#bots', 'me', 'helga stfu for 30', 'stfu', ['for', '30'])
    reactor.callLater.assertCalledWith(30*60, stfu.auto_unsilence, client, '#bots', 30*60)


def test_stfu_unsilences_channel():
    client = Mock()
    stfu.silenced = set(['#bots'])
    stfu.stfu(client, '#bots', 'me', 'helga speak', 'speak', [])
    assert '#bots' not in stfu.silenced
