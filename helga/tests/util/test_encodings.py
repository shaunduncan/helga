# -*- coding: utf8 -*-
from helga.util.encodings import (from_unicode,
                                  from_unicode_args,
                                  to_unicode,
                                  to_unicode_args)


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


def test_to_unicode_args():
    @to_unicode_args
    def foo(arg1, arg2, arg3):
        return arg1, arg2, arg3

    snowman = u'☃'
    bytes = '\xe2\x98\x83'
    # None here to ensure bad things don't happen
    retval = foo(bytes, 'foo', None)

    assert retval[0] == snowman
    assert retval[1] == u'foo'
    assert retval[2] is None
    assert isinstance(retval[0], unicode)
    assert isinstance(retval[1], unicode)


def test_from_unicode_args():
    @from_unicode_args
    def foo(arg1, arg2, arg3):
        return arg1, arg2, arg3

    snowman = u'☃'
    bytes = '\xe2\x98\x83'
    # None here to ensure bad things don't happen
    retval = foo(snowman, 'foo', None)

    assert retval[0] == bytes
    assert retval[1] == 'foo'
    assert retval[2] is None
    assert isinstance(retval[0], str)
    assert isinstance(retval[1], str)
