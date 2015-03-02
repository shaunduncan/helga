"""
Utilities for working with unicode and/or byte strings
"""
from decorator import decorator


def to_unicode(bytestr, errors='ignore'):
    """
    Safely convert a byte string to unicode by first checking if it already is unicode before decoding.
    This function assumes UTF-8 for byte strings and by default will ignore any decoding errors.

    :param bytestr: either a byte string or unicode string
    :param errors: a string indicating how decoding errors should be handled
                   (i.e. 'strict', 'ignore', 'replace')
    """
    if isinstance(bytestr, unicode):
        return bytestr
    return bytestr.decode('utf-8', errors)


def from_unicode(unistr, errors='ignore'):
    """
    Safely convert unicode to a byte string by first checking if it already is a byte string before
    encoding. This function assumes UTF-8 for byte strings and by default will ignore any encoding errors.

    :param unistr: either unicode or a byte string
    :param errors: a string indicating how encoding errors should be handled
                   (i.e. 'strict', 'ignore', 'replace')
    """
    if not isinstance(unistr, unicode):
        return unistr
    return unistr.encode('utf-8', errors)


@decorator
def to_unicode_args(fn, *args, **kwargs):
    """
    Decorator used to safely convert a function's positional arguments from byte strings to unicode
    """
    args = list(args)
    for i, val in enumerate(args):
        if isinstance(val, str):
            args[i] = to_unicode(val)
    return fn(*args, **kwargs)


@decorator
def from_unicode_args(fn, *args, **kwargs):
    """
    Decorator used to safely convert a function's positional arguments from unicode to byte strings
    """
    args = list(args)
    for i, val in enumerate(args):
        if isinstance(val, unicode):
            args[i] = from_unicode(val)
    return fn(*args, **kwargs)
