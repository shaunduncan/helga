# -*- coding: utf8 -*-
from datetime import datetime

from mock import patch
from pretend import stub

from helga.plugins import facts


def test_term_regex():
    pat = facts.term_regex('foo')

    assert bool(pat.match('foo'))
    assert not bool(pat.match('will not match foo'))


def test_term_regex_handles_unicode():
    snowman = u'☃'
    pat = facts.term_regex(snowman)
    assert bool(pat.match(snowman))
    assert not bool(pat.match('no snowman for you :('))


@patch('helga.plugins.facts.db')
def test_show_fact_no_record(db):
    db.facts.find_one.return_value = None
    assert facts.show_fact('foo') is None


@patch('helga.plugins.facts.db')
def test_show_fact_without_author(db):
    fact = {
        'term': 'foo',
        'fact': 'foo is bar',
    }

    db.facts.find_one.return_value = fact
    assert facts.show_fact('foo') == 'foo is bar'


@patch('helga.plugins.facts.db')
def test_show_fact_without_set_time(db):
    fact = {
        'term': 'foo',
        'fact': 'foo is bar',
        'set_by': 'sduncan',
    }

    db.facts.find_one.return_value = fact
    assert facts.show_fact('foo') == 'foo is bar (sduncan)'


@patch('helga.plugins.facts.db')
def test_show_fact(db):
    fact = {
        'term': 'foo',
        'fact': 'foo is bar',
        'set_by': 'sduncan',
        'set_date': 1360849874.686594,  # 02/14/2013 08:51AM
    }

    db.facts.find_one.return_value = fact
    assert facts.show_fact('foo') == 'foo is bar (sduncan on 02/14/2013 08:51AM)'


@patch('helga.plugins.facts.db')
def test_show_fact_handles_unicode(db):
    fact = {
        'term': u'☃',
        'fact': u'☃ is unicode snowman',
        'set_by': 'sduncan',
        'set_date': 1360849874.686594,  # 02/14/2013 08:51AM
    }

    db.facts.find_one.return_value = fact
    assert facts.show_fact(u'☃') == u'☃ is unicode snowman (sduncan on 02/14/2013 08:51AM)'


@patch('helga.plugins.facts.db')
def test_show_fact_set_date_is_datetime(db):
    fact = {
        'term': 'foo',
        'fact': 'foo is bar',
        'set_by': 'sduncan',
        'set_date': datetime(2013, 2, 14, 8, 51),
    }

    db.facts.find_one.return_value = fact
    assert facts.show_fact('foo') == 'foo is bar (sduncan on 02/14/2013 08:51AM)'


@patch('helga.plugins.facts.settings')
@patch('helga.plugins.facts.add_fact')
def test_facts_match_with_nick(add_fact, settings):
    settings.FACTS_REQUIRE_NICKNAME = True
    client = stub(nickname='helga')

    # The format the regex will use
    found = [('helga: foo bar', 'is', '', 'this is the response')]
    add_fact.return_value = 'ok'

    assert 'ok' == facts.facts_match(client, '', '', '', found)
    add_fact.assert_called_with('foo bar', 'foo bar is this is the response', '')


@patch('helga.plugins.facts.settings')
@patch('helga.plugins.facts.add_fact')
def test_facts_match_requires_nick(add_fact, settings):
    settings.FACTS_REQUIRE_NICKNAME = True
    client = stub(nickname='helga')

    # The format the regex will use
    found = [('foo bar', 'is', '', 'this is the response')]
    add_fact.return_value = 'ok'

    assert facts.facts_match(client, '', '', '', found) is None


def test_facts_match_found_is_show_fact():
    facts.show_fact = lambda s: s
    assert facts.facts_match(None, '', '', '', ['foo']) == 'foo'
    assert facts.facts_match(None, '', '', '', [u'☃']) == u'☃'


@patch('helga.plugins.facts.settings')
@patch('helga.plugins.facts.add_fact')
def test_facts_match_handles_unicode(add_fact, settings):
    add_fact.return_value = 'ok'
    settings.FACTS_REQUIRE_NICKNAME = False
    client = stub(nickname='helga')

    snowman = u'☃'
    found_args = [
        [(snowman, 'is', '', 'here is a snowman')],
        [(snowman, 'is', '<reply>', 'here is a snowman')],
    ]
    for args in found_args:
        assert 'ok' == facts.facts_match(client, '', '', '', args)

    # Handle unicode with nick checking
    settings.FACTS_REQUIRE_NICKNAME = True
    for args in found_args:
        # prepend the nick
        with_nick = [['helga ' + args[0][0]] + list(args[0][1:])]
        assert facts.facts_match(client, '', '', '', args) is None
        assert 'ok' == facts.facts_match(client, '', '', '', with_nick)


@patch('helga.plugins.facts.add_fact')
def test_facts_as_reply(add_fact):
    # The format the regex will use
    found = [('foo bar', 'is', '<reply>', 'this is the response')]
    add_fact.return_value = 'ok'

    assert 'ok' == facts.facts_match('', '', '', '', found)
    add_fact.assert_called_with('foo bar', 'this is the response', '')


@patch('helga.plugins.facts.add_fact')
def test_facts(add_fact):
    # The format the regex will use
    found = [('foo bar', 'is', '', 'this is the response')]
    add_fact.return_value = 'ok'

    assert 'ok' == facts.facts_match('', '', '', '', found)
    add_fact.assert_called_with('foo bar', 'foo bar is this is the response', '')


@patch('helga.plugins.facts.db')
def test_add_fact_does_nothing_when_found(db):
    db.facts.find.return_value = db
    db.count.return_value = 1
    facts.add_fact('foo', 'bar', 'baz')
    assert not db.facts.insert.called


@patch('helga.plugins.facts.db')
@patch('helga.plugins.facts.time')
def test_add_fact(time, db):
    time.time.return_value = 1
    db.facts.find.return_value = db
    db.count.return_value = 0
    facts.add_fact('foo', 'bar', 'baz')
    db.facts.insert.assert_called_with({
        'term': 'foo',
        'fact': 'bar',
        'set_by': 'baz',
        'set_date': 1,
    })


@patch('helga.plugins.facts.db')
def test_forget_fact(db):
    facts.forget_fact('foo')
    db.facts.remove.assert_called_with({
        'term': facts.term_regex('foo'),
    })


def test_facts_command():
    facts.forget_fact = lambda s: s
    args = ['foo', 'bar', 'baz']
    assert 'foo bar baz' == facts.facts_command(None, '#bots', 'me', '!forget foo', 'forget', args)
    assert facts.facts_command(None, '#bots', 'me', '!forget foo', 'foobar', args) is None


@patch('helga.plugins.facts.forget_fact')
@patch('helga.plugins.facts.add_fact')
def test_replace_fact(add, forget):
    facts.replace_fact('term', 'definition', author='person')
    forget.assert_called_with('term')
    add.assert_called_with(
        'term',
        'definition',
        'person',
    )


def test_replace_facts_command():
    facts.replace_fact = lambda x, y, author: (x, y, author)
    args = ['term1', 'term2', '<with>', 'def1', 'def2']
    assert (u'term1 term2', u'def1 def2', u'me') == facts.facts_command(
        None, '#bots', 'me', '!replace term1 term2 <with> def1 def2', 'replace', args
    )


def test_replace_facts_missing_pipe_command():
    facts.replace_fact = lambda x, y, author: (x, y, author)
    args = ['term1', 'term2', 'def1', 'def2']
    assert (u'No definition supplied.') == facts.facts_command(
        None, '#bots', 'me', '!replace term1 term2 <with> def1 def2', 'replace', args
    )


@patch('helga.plugins.facts.facts_match')
@patch('helga.plugins.facts.facts_command')
def test_facts_plugin(cmd, match):
    cmd.return_value = 'command'
    match.return_value = 'match'

    assert 'command' == facts.facts(None, '#bots', 'me', 'command', 'foo', 'bar')
    assert 'match' == facts.facts(None, '#bots', 'me', 'match', 'match')
