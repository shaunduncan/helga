from mock import patch

from helga.plugins import icanhazascii


mock_animalz = {r'foo': 'bar'}


@patch('helga.plugins.icanhazascii.ANIMALZ', mock_animalz)
def test_find_animal_is_not_too_aggressive():
    assert icanhazascii.find_animal('this is a foo message') is None


@patch('helga.plugins.icanhazascii.ANIMALZ', mock_animalz)
def test_find_animal_no_match():
    assert icanhazascii.find_animal('bar') is None


@patch('helga.plugins.icanhazascii.ANIMALZ', mock_animalz)
def test_find_animal_returns_ascii_string():
    assert icanhazascii.find_animal('foo') == 'bar'


def test_plugin_flood_control():
    assert icanhazascii.icanhazascii(None, '#bots', 'me', 'foo', 'bar') is not None
    assert icanhazascii.icanhazascii(None, '#bots', 'me', 'foo', 'bar') is None
