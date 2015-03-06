from mock import patch

from helga.plugins import version


@patch('helga.plugins.version.helga')
def test_version(helga):
    helga.__version__ = '1.0'
    assert version.version() == 'Helga version 1.0'
