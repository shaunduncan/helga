import os
import sys

import pytest

from helga import settings


def test_configure_execfile(tmpdir):
    file = tmpdir.join('foo.py')
    file.write('MY_CUSTOM_SETTING = "foo"')

    assert not hasattr(settings, 'MY_CUSTOM_SETTING')
    settings.configure(str(file))
    assert settings.MY_CUSTOM_SETTING == 'foo'
    delattr(settings, 'MY_CUSTOM_SETTING')


def test_configure_import(tmpdir):
    file = tmpdir.join('foo.py')
    file.write('MY_CUSTOM_SETTING = "foo"')

    sys.path.insert(0, str(tmpdir))
    filename = os.path.basename(str(file)).replace('.py', '')

    assert not hasattr(settings, 'MY_CUSTOM_SETTING')
    settings.configure(filename)
    assert settings.MY_CUSTOM_SETTING == 'foo'
    delattr(settings, 'MY_CUSTOM_SETTING')


def test_configure_import_raises():
    with pytest.raises(ImportError):
        settings.configure('foo.bar')
