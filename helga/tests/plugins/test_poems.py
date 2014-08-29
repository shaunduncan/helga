# -*- coding: utf8 -*-
import re

import pytest

from mock import Mock, patch, call

from helga.plugins import poems, ResponseNotReady


@patch('helga.plugins.poems.get_random_line')
def test_fix_repitition_replaces(get_random_line):
    poem = ['foo', 'bar', 'foo']
    get_random_line.return_value = 'baz'
    poem = poems.fix_repitition(poem)

    assert poem == ['foo', 'bar', 'baz']


@patch('helga.plugins.poems.get_random_line')
def test_fix_repititions_gives_up_after_retry(get_random_line):
    poem = ['foo', 'bar', 'foo']
    get_random_line.return_value = 'foo'
    poem = poems.fix_repitition(poem)

    assert poem == ['foo', 'bar', 'foo']
    assert poems.get_random_line.call_count == 2


@patch('helga.plugins.poems.get_random_line')
def test_fix_repitition_does_not_replace(get_random_line):
    poem = ['foo', 'bar', 'baz']
    poem = poems.fix_repitition(poem)

    assert poem == ['foo', 'bar', 'baz']
    assert not poems.get_random_line.called


@patch('helga.plugins.poems.db')
def test_add(db):
    poems.add(5, 'foobar')
    assert db.haiku.insert.called


@patch('helga.plugins.poems.use')
@patch('helga.plugins.poems.add')
def test_add_use(add, use):
    poems.add_use(5, 'foo')
    add.assert_called_with(5, 'foo', author=None)
    use.assert_called_with(5, 'foo')


@patch('helga.plugins.poems.db')
def test_remove(db):
    poems.remove(5, 'foobar')
    assert db.haiku.remove.called


@patch('helga.plugins.poems.db')
def test_get_random_line(db):
    result = Mock()
    result.sort = result
    result.count.return_value = 1
    result.limit.return_value = result
    result.skip.return_value = result
    result.next.return_value = {'message': 'fives1'}

    fake_find = Mock(return_value=result)

    db.haiku.find = fake_find
    line = poems.get_random_line(5)
    assert line == 'fives1'


@patch('helga.plugins.poems.db')
def test_get_random_line_returns_none(db):
    db.haiku.find.return_value = db
    db.count.return_value = 0
    assert poems.get_random_line(5) is None


@patch('helga.plugins.poems.db')
def test_get_random_line_with_author(db):
    result = Mock()
    result.sort = result
    result.count.return_value = 1
    result.limit.return_value = result
    result.skip.return_value = result
    result.next.return_value = {'message': u'fives☃'}  # Ensure unicode test

    fake_find = Mock(return_value=result)

    db.haiku.find = fake_find
    poems.get_random_line(5, by='me')
    fake_find.assert_called_with({
        'syllables': 5,
        'author': {
            '$regex': re.compile('me', re.I)
        }
    })


@patch('helga.plugins.poems.db')
def test_get_random_line_with_search(db):
    result = Mock()
    result.sort = result
    result.count.return_value = 1
    result.limit.return_value = result
    result.skip.return_value = result
    result.next.return_value = {'message': 'fives1'}

    fake_find = Mock(return_value=result)

    db.haiku.find = fake_find
    poems.get_random_line(5, about='me')
    fake_find.assert_called_with({
        'syllables': 5,
        'message': {
            '$regex': re.compile('me', re.I)
        }
    })


@patch('helga.plugins.poems.db')
def test_get_random_line_with_search_or_author_retries(db):
    result = Mock()
    result.sort = result
    result.count.side_effect = (0, 1)
    result.limit.return_value = result
    result.skip.return_value = result
    result.next.return_value = {'message': 'fives1'}

    fake_find = Mock(return_value=result)

    db.haiku.find = fake_find
    poems.get_random_line(5, about='me')
    assert fake_find.call_count == 2
    assert fake_find.call_args_list[-1] == call({'syllables': 5})


@patch('helga.plugins.poems.add')
@patch('helga.plugins.poems.make_poem')
def test_use_fives(make_poem, add):
    make_poem.return_value = ['one', 'two', 'three']
    poem = poems.use(5, 'foo')
    assert 'foo' in (poem[0], poem[2])


@patch('helga.plugins.poems.add')
@patch('helga.plugins.poems.make_poem')
def test_use_fives_tanka(make_poem, add):
    make_poem.return_value = ['one', 'two', 'three', 'four', 'five']
    poem = poems.use(5, 'foo', poem_type='tanka')
    assert 'foo' in (poem[0], poem[2])


@patch('helga.plugins.poems.add')
@patch('helga.plugins.poems.make_poem')
def test_use_fives_does_not_duplicate(make_poem, add):
    make_poem.return_value = ['foo', 'two', 'three']
    poem = poems.use(5, 'foo')
    assert poem[0] == 'foo'
    assert poem[2] != 'foo'


@patch('helga.plugins.poems.add')
@patch('helga.plugins.poems.make_poem')
def test_use_sevens(make_poem, add):
    make_poem.return_value = ['one', 'two', 'three']
    poem = poems.use(7, 'foo')
    assert poem[1] == 'foo'


@patch('helga.plugins.poems.add')
@patch('helga.plugins.poems.make_poem')
def test_use_sevens_tanka(make_poem, add):
    make_poem.return_value = ['one', 'two', 'three', 'four', 'five']
    poem = poems.use(7, 'foo', poem_type='tanka')
    assert 'foo' in (poem[1], poem[3], poem[4])


@patch('helga.plugins.poems.get_random_line')
def test_make_poem(get_random_line):
    with patch.object(poems, 'fix_repitition', lambda s: s):
        # Poems have a random ordering
        with patch('helga.plugins.poems.random') as random:
            random.choice.side_effect = [0, 1]

            get_random_line.side_effect = ['one', 'two', 'three']
            assert poems.make_poem() == ['one', 'two', 'three']

            get_random_line.side_effect = ['one', 'two', 'three']
            assert poems.make_poem() == ['three', 'two', 'one']


@patch('helga.plugins.poems.get_random_line')
def test_make_poem_tanka(get_random_line):
    get_random_line.side_effect = ['one', 'two', 'three', 'four', 'five']
    poem = poems.make_poem(poem_type='tanka')

    # Poems have a random ordering
    assert poem in (
        ['one', 'two', 'three', 'four', 'five'],
        ['three', 'two', 'one', 'four', 'five'],
    )


@patch('helga.plugins.poems.get_random_line')
def test_make_poem_none_if_incomplete(get_random_line):
    get_random_line.side_effect = ['foo', 'bar', '']
    assert poems.make_poem(poem_type='haiku') is None


@patch('helga.plugins.poems.fix_repitition')
@patch('helga.plugins.poems.get_random_line')
def test_make_poem_adds_about_or_by_kwargs(get_random_line, fix_rep):
    poem = ['one', 'two', 'three']
    fix_rep.return_value = poem
    get_random_line.side_effect = poem
    poems.make_poem(about='me')
    args, kwargs = fix_rep.call_args
    assert sorted(args[0]) == sorted(poem)
    assert kwargs == {'about': 'me'}

    poem = ['one', 'two', 'three']
    get_random_line.side_effect = poem
    poems.make_poem(by='me')
    args, kwargs = fix_rep.call_args
    assert sorted(args[0]) == sorted(poem)
    assert kwargs == {'by': 'me'}


@patch('helga.plugins.poems.make_poem')
def test_poems_no_args_returns_poem(make_poem):
    poem = 'this is my poem'
    make_poem.return_value = poem
    assert poem == poems.poems(Mock(), '#bots', 'me', 'message', 'haiku', [])
    assert poem == poems.last_poem['#bots']
    make_poem.assert_called_with(poem_type='haiku')


@patch('helga.plugins.poems.make_poem')
def test_poems_about_or_by_subcommand(make_poem):
    args = [Mock(), '#bots', 'me', 'message', 'haiku']
    for extra in (['about', u'☃'], ['by', 'foo']):
        make_poem.reset_mock()
        poems.poems(*(args + [extra]))
        kwargs = {
            'poem_type': 'haiku',
            extra[0]: extra[1]
        }
        make_poem.assert_called_with(**kwargs)


@patch('helga.plugins.poems.blame')
def test_poems_blame_subcommand(blame):
    poems.poems(Mock(nickname='helga'), '#bots', 'me', 'message', 'haiku', ['blame'])
    blame.assert_called_with('#bots', requested_by='me', default_author='helga')


@patch('helga.plugins.poems.reactor')
def test_poems_tweet_subcommand(reactor):
    client = Mock()
    with pytest.raises(ResponseNotReady):
        poems.poems(client, '#bots', 'me', 'message', 'haiku', ['tweet'])
        reactor.assert_called_with(0, poems.tweet, client, '#bots', 'me')


@patch('helga.plugins.poems.add')
def test_poems_add_subcommand(add):
    subcmd_args = ['add', 'fives', 'unicode', u'☃']
    args = [Mock(), '#bots', 'me', 'message', 'haiku', subcmd_args]
    poems.poems(*args)
    add.assert_called_with(5, u'unicode ☃', 'me')


@patch('helga.plugins.poems.add_use')
def test_poems_add_use_subcommand(add_use):
    add_use.return_value = 'a poem'
    subcmd_args = ['add_use', 'fives', 'unicode', u'☃']
    args = [Mock(), '#bots', 'me', 'message', 'haiku', subcmd_args]
    poems.poems(*args)
    add_use.assert_called_with(5, u'unicode ☃', 'me')
    assert poems.last_poem['#bots'] == 'a poem'


@patch('helga.plugins.poems.use')
def test_poems_use_subcommand(use):
    use.return_value = 'a poem'
    subcmd_args = ['use', 'fives', 'unicode', u'☃']
    args = [Mock(), '#bots', 'me', 'message', 'haiku', subcmd_args]
    poems.poems(*args)
    use.assert_called_with(5, u'unicode ☃')
    assert poems.last_poem['#bots'] == 'a poem'


@patch('helga.plugins.poems.remove')
def test_poems_remove_subcommand(remove):
    subcmd_args = ['remove', 'fives', 'unicode', u'☃']
    args = [Mock(), '#bots', 'me', 'message', 'haiku', subcmd_args]
    poems.poems(*args)
    remove.assert_called_with(5, u'unicode ☃')


@patch('helga.plugins.poems.claim')
def test_poems_claim_subcommand(claim):
    subcmd_args = ['claim', 'fives', 'unicode', u'☃']
    args = [Mock(), '#bots', 'me', 'message', 'haiku', subcmd_args]
    poems.poems(*args)
    claim.assert_called_with(5, u'unicode ☃', 'me')


@patch('helga.plugins.poems.db')
def test_claim(db):
    resp = poems.claim(5, u'unicode snowman ☃', author='me')
    db.haiku.update.assert_called_with({'message': u'unicode snowman ☃'},
                                       {'$set': {'author': 'me'}})
    assert resp == u'me has claimed the line: unicode snowman ☃'


@patch('helga.plugins.poems.db')
def test_claim_unknown_line(db):
    db.haiku.update.side_effect = Exception
    resp = poems.claim(5, u'unicode snowman ☃', author='me')
    assert resp == "Sorry, I don't know that line."


def test_tweet_with_no_poem():
    client = Mock()
    poems.last_poem['#bots'] = None
    poems.tweet(client, '#bots', 'me')
    client.msg.assert_called_with('#bots', "me, why don't you try making one first")


@patch('helga.plugins.poems.send_tweet')
def test_tweet_with_failure(send_tweet):
    client = Mock()
    send_tweet.return_value = None
    poems.last_poem['#bots'] = ['foobar']
    poems.tweet(client, '#bots', 'me')
    client.msg.assert_called_with('#bots', "me, that probably did not work :(")


@patch('helga.plugins.poems.send_tweet')
def test_tweet(send_tweet):
    client = Mock()
    send_tweet.return_value = 'blah'
    poems.last_poem['#bots'] = ['foobar']
    poems.tweet(client, '#bots', 'me')
    client.msg.assert_called_with('#bots', 'blah')


def test_blame_with_no_poem():
    poems.last_poem['#bots'] = None
    resp = poems.blame('#bots', 'me')
    assert resp == "me, why don't you try making one first"


@patch('helga.plugins.poems.db')
def test_blame_uses_default_author(db):
    db.haiku.find_one.side_effect = Exception
    poems.last_poem['#bots'] = ['foo', 'bar', 'baz']
    resp = poems.blame('#bots', 'me', default_author='helga')
    assert resp == 'The last poem was brought to you by (in order): helga, helga, helga'


@patch('helga.plugins.poems.db')
def test_blame(db):
    poems.last_poem['#bots'] = ['foo', 'bar', 'baz']
    db.haiku.find_one.side_effect = [
        {'author': 'foo'},
        {'author': u'☃'},  # Test unicode
        {},  # No author
    ]
    resp = poems.blame('#bots', 'me', default_author='helga')
    assert resp == u'The last poem was brought to you by (in order): foo, ☃, helga'


@patch('helga.plugins.poems.db')
def test_blame_after_use_uses_last_author(db):
    poems.last_use['#bots'] = ('me', 'three')
    poems.last_poem['#bots'] = ['one', 'two', 'three']
    db.haiku.find_one.side_effect = [
        {'author': 'foo'},
        {'author': 'bar'},
        None
    ]

    ret = poems.blame('#bots', 'sduncan', default_author='helga')
    assert ret == 'The last poem was brought to you by (in order): foo, bar, me'


@patch('helga.plugins.poems.db')
def test_blame_after_use_when_no_last_used(db):
    # Edge case test
    poems.last_use['#bots'] = tuple()
    poems.last_poem['#bots'] = ['one', 'two', 'three']
    db.haiku.find_one.side_effect = [
        {'author': 'foo'},
        {'author': 'bar'},
        None
    ]

    ret = poems.blame('#bots', 'sduncan', default_author='helga')
    assert ret == 'The last poem was brought to you by (in order): foo, bar, helga'
