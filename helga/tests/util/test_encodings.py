# encoding: utf-8
from helga.util.encodings import to_unicode, from_unicode


def test_to_unicode_with_unicode_string():
    snowman = u'☃'
    retval = to_unicode(snowman)
    assert snowman == retval
    assert isinstance(retval, unicode)


def test_to_unicode_with_byte_string():
    snowman = u'☃'
    bytes = '\xe2\x98\x83'
    retval = to_unicode(bytes)
    assert snowman == retval
    assert isinstance(retval, unicode)


def test_from_unicode_with_unicode_string():
    snowman = u'☃'
    bytes = '\xe2\x98\x83'
    retval = from_unicode(snowman)
    assert bytes == retval
    assert isinstance(retval, str)


def test_from_unicode_with_byte_string():
    bytes = '\xe2\x98\x83'
    retval = from_unicode(bytes)
    assert bytes == retval
    assert isinstance(retval, str)
