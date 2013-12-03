"""
Tests for helga.plugins
"""
from helga.plugins import command, match


def test_match_simple():
    @match('foo')
    def foo(chan, nick, msg, found):
        return 'bar'

    assert 'bar' == foo('#bots', 'me', 'this is a foo message')
    assert foo('#bots', 'me', 'this is a baz message') is None


def test_match_regex():
    @match('^foo is (\d+)')
    def foo(chan, nick, msg, found):
        return found[0]

    assert '123' == foo('#bots', 'me', 'foo is 123')
    assert foo('#bots', 'me', 'foo is bar') is None


def test_match_callable():
    @match(lambda x: x.startswith('foo'))
    def foo(chan, nick, msg, found):
        return 'bar'

    assert 'bar' == foo('#bots', 'me', 'foo at the start')
    assert foo('#bots', 'me', 'not at the start foo') is None
