from mock import patch
from pretend import stub

from helga.plugins import facts


def test_term_regex():
    pat = facts.term_regex('foo')

    assert bool(pat.match('foo'))
    assert not bool(pat.match('will not match foo'))


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


@patch('helga.plugins.facts.settings')
@patch('helga.plugins.facts.add_fact')
def test_facts_match_with_nick(add_fact, settings):
    settings.FACTS_REQUIRE_NICKNAME = True
    client = stub(nickname='helga')

    # The format the regex will use
    found = [('helga: foo bar', 'is', '', 'this is the response')]
    add_fact.return_value = 'ok'

    assert 'ok' == facts.facts_match(client, '', '', '', found)
    add_fact.assertCalledWith('foo bar', 'foo bar is this is the response')


@patch('helga.plugins.facts.settings')
@patch('helga.plugins.facts.add_fact')
def test_facts_match_requires_nick(add_fact, settings):
    settings.FACTS_REQUIRE_NICKNAME = True
    client = stub(nickname='helga')

    # The format the regex will use
    found = [('foo bar', 'is', '', 'this is the response')]
    add_fact.return_value = 'ok'

    assert facts.facts_match(client, '', '', '', found) is None


@patch('helga.plugins.facts.add_fact')
def test_facts_as_reply(add_fact):
    # The format the regex will use
    found = [('foo bar', 'is', '<reply>', 'this is the response')]
    add_fact.return_value = 'ok'

    assert 'ok' == facts.facts_match('', '', '', '', found)
    add_fact.assertCalledWith('foo bar', 'this is the response')


@patch('helga.plugins.facts.add_fact')
def test_facts(add_fact):
    # The format the regex will use
    found = [('foo bar', 'is', '', 'this is the response')]
    add_fact.return_value = 'ok'

    assert 'ok' == facts.facts_match('', '', '', '', found)
    add_fact.assertCalledWith('foo bar', 'foo bar is this is the response')
