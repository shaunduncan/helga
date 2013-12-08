import re

from helga.plugins import loljava


def test_make_bullshit_java_thing():
    assert loljava.make_bullshit_java_thing(None, '#bots', 'me', 'java', ['java'])


def test_regex_matches_java():
    plugin = loljava.make_bullshit_java_thing._plugins[0]
    assert re.match(plugin.pattern, 'java')
    assert re.match(plugin.pattern, 'loljava')


def test_regex_ignores_javascript():
    plugin = loljava.make_bullshit_java_thing._plugins[0]
    assert not re.match(plugin.pattern, 'javascript')
