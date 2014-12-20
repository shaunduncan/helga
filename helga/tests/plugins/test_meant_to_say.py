import re

from collections import defaultdict
from pretend import stub

from helga.plugins import meant_to_say


def test_meant_to_say_none_when_no_last_message():
    client = stub(last_message=defaultdict(dict))
    assert meant_to_say.meant_to_say(client, '#bots', 'me', 's/foo/bar', [('foo', 'bar', '')]) is None


def test_meant_to_say_regex():
    plugin = meant_to_say.meant_to_say._plugins[0]
    assert bool(re.match(plugin.pattern, 's/foo/bar'))
    assert bool(re.match(plugin.pattern, 's/foo/bar/'))


def test_meant_to_say_returns_modified():
    client = stub(last_message=defaultdict(dict))
    client.last_message['#bots']['me'] = 'this is a foo message'

    resp = meant_to_say.meant_to_say(client, '#bots', 'me', 's/foo/bar', [('foo', 'bar', '')])
    assert resp == 'me meant to say: this is a bar message'


def test_meant_to_say_none_when_not_modified():
    client = stub(last_message=defaultdict(dict))
    client.last_message['#bots']['me'] = 'this is a message'

    assert meant_to_say.meant_to_say(client, '#bots', 'me', 's/foo/bar', [('foo', 'bar', '')]) is None


class TestMeantToSay(object):

    def setup(self):
        self.client = stub(last_message=defaultdict(dict))

    def test_single_replacement(self):
        self.client.last_message['#bots']['me'] = 'this is a foo message foo'

        resp = meant_to_say.meant_to_say(
            self.client,
            '#bots',
            'me',
            's/foo/bar/',
            [('foo', 'bar', '/')]
        )
        assert resp == 'me meant to say: this is a bar message foo'

    def test_g(self):
        self.client.last_message['#bots']['me'] = 'this is a foo message foo'

        resp = meant_to_say.meant_to_say(
            self.client,
            '#bots',
            'me',
            's/foo/bar/g',
            [('foo', 'bar', '/g')]
        )
        assert resp == 'me meant to say: this is a bar message bar'

    def test_i(self):
        self.client.last_message['#bots']['me'] = 'this is a FOO message'

        resp = meant_to_say.meant_to_say(
            self.client,
            '#bots',
            'me',
            's/foo/bar/i',
            [('foo', 'bar', '/i')]
        )
        assert resp == 'me meant to say: this is a bar message'

    def test_i_with_garbage_flags(self):
        self.client.last_message['#bots']['me'] = 'this is a FOO message'

        resp = meant_to_say.meant_to_say(
            self.client,
            '#bots',
            'me',
            's/foo/bar/iasdf',
            [('foo', 'bar', '/iasdf')]
        )
        assert resp == 'me meant to say: this is a bar message'

    def test_gi(self):
        self.client.last_message['#bots']['me'] = 'this is a FOO message foo'

        resp = meant_to_say.meant_to_say(
            self.client,
            '#bots',
            'me',
            's/foo/bar/gi',
            [('foo', 'bar', '/gi')]
        )
        assert resp == 'me meant to say: this is a bar message bar'

    def test_gi_with_garbage_flags(self):
        self.client.last_message['#bots']['me'] = 'this is a FOO message foo'

        resp = meant_to_say.meant_to_say(
            self.client,
            '#bots',
            'me',
            's/foo/bar/gic',
            [('foo', 'bar', '/gic')]
        )
        assert resp == 'me meant to say: this is a bar message bar'
