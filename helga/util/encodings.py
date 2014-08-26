"""
Utils for deailing with encode/decode and unicode pain
"""


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
