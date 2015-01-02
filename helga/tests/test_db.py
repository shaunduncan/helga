from mock import patch, Mock

from helga import db
from pymongo.errors import ConnectionFailure


@patch('helga.db.MongoClient')
@patch('helga.db.settings')
def test_connect_returns_none_on_failure(settings, mongo):
    settings.DATABASE = {
        'HOST': 'localhost',
        'PORT': '1234',
    }

    mongo.side_effect = ConnectionFailure
    assert db.connect() == (None, None)


@patch('helga.db.MongoClient')
@patch('helga.db.settings')
def test_connect_authenticates(settings, mongo):
    settings.DATABASE = {
        'HOST': 'localhost',
        'PORT': '1234',
        'USERNAME': 'foo',
        'PASSWORD': 'bar',
        'DB': 'baz',
    }

    mongo.return_value = mongo

    database = Mock()
    mongo.__getitem__ = Mock()
    mongo.__getitem__.return_value = database

    db.connect()
    database.authenticate.assert_called_with('foo', 'bar')


@patch('helga.db.MongoClient')
@patch('helga.db.settings')
def test_connect(settings, mongo):
    settings.DATABASE = {
        'HOST': 'localhost',
        'PORT': '1234',
        'DB': 'baz',
    }

    mongo.return_value = mongo

    database = Mock()
    mongo.__getitem__ = Mock()
    mongo.__getitem__.return_value = database

    assert db.connect() == (mongo, database)
    mongo.__getitem__.assert_called_with('baz')
