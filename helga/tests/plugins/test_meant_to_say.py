import re

from collections import defaultdict
from pretend import stub

from helga.plugins import meant_to_say


def test_meant_to_say_none_when_no_last_message():
    client = stub(last_message=defaultdict(dict))
    assert meant_to_say.meant_to_say(client, '#bots', 'me', 's/foo/bar', [('foo', 'bar')]) is None


def test_meant_to_say_regex():
    plugin = meant_to_say.meant_to_say._plugins[0]
    assert bool(re.match(plugin.pattern, 's/foo/bar'))
    assert bool(re.match(plugin.pattern, 's/foo/bar/'))


def test_meant_to_say_returns_modified():
    client = stub(last_message=defaultdict(dict))
    client.last_message['#bots']['me'] = 'this is a foo message'

    resp = meant_to_say.meant_to_say(client, '#bots', 'me', 's/foo/bar', [('foo', 'bar')])
    assert resp == 'me meant to say: this is a bar message'


def test_meant_to_say_none_when_not_modified():
    client = stub(last_message=defaultdict(dict))
    client.last_message['#bots']['me'] = 'this is a message'

    assert meant_to_say.meant_to_say(client, '#bots', 'me', 's/foo/bar', [('foo', 'bar')]) is None
