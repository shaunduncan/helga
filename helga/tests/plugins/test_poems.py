from mock import Mock, patch

from helga.plugins import poems


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
    get_random_line.side_effect = ['one', 'two', 'three', 'four', 'five']
    poem = poems.make_poem()

    # Poems have a random ordering
    assert poem in (
        ['one', 'two', 'three'],
        ['three', 'two', 'one'],
    )


@patch('helga.plugins.poems.get_random_line')
def test_make_poem_tanka(get_random_line):
    get_random_line.side_effect = ['one', 'two', 'three', 'four', 'five']
    poem = poems.make_poem(poem_type='tanka')

    # Poems have a random ordering
    assert poem in (
        ['one', 'two', 'three', 'four', 'five'],
        ['three', 'two', 'one', 'four', 'five'],
    )
