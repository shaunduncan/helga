"""
Utils for deailing with encode/decode and unicode pain
"""
from functools import wraps


def to_unicode(bytestr, errors='ignore'):
    """
    Enforces a byte string to be unicode. If it already is unicode, no
    action is taken. Otherwise, the byte string is decoded as UTF-8
    """
    if isinstance(bytestr, unicode):
        return bytestr
    return bytestr.decode('utf-8', errors)


def from_unicode(unistr, errors='ignore'):
    """
    Enforces a unicode string to be a byte string. If it already is a byte
    string, no action is taken. Otherwise, it is encoded as UTF-8
    """
    if not isinstance(unistr, unicode):
        return unistr
    return unistr.encode('utf-8', errors)


def to_unicode_args(fn):
    """
    Automatically converts all positional byte string arguments to unicode
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        args = list(args)
        for i, val in enumerate(args):
            if isinstance(val, str):
                args[i] = to_unicode(val)
        return fn(*args, **kwargs)
    return wrapper


def from_unicode_args(fn):
    """
    Automatically converts all positional unicode arguments to byte strings
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        args = list(args)
        for i, val in enumerate(args):
            if isinstance(val, unicode):
                args[i] = from_unicode(val)
        return fn(*args, **kwargs)
    return wrapper
