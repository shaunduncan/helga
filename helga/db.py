"""
`pymongo`_ connection objects and utilities

.. attribute:: client

    A `pymongo.mongo_client.MongoClient` instance, the connection client to MongoDB

.. attribute:: db

    A `pymongo.database.Database` instance, the default MongoDB database to use


.. _`pymongo`: http://api.mongodb.org/python/current/
"""
import warnings


from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from helga import settings


def connect():
    """
    Connect to a MongoDB instance, if helga is configured to do so (see setting
    :data:`~helga.settings.DATABASE`). This will return the MongoDB client as well
    as the default database as configured.

    :returns: A two-tuple of (`pymongo.MongoClient`, `pymongo.database.Database`)
    """
    db_settings = getattr(settings, 'DATABASE', {})

    try:
        client = MongoClient(db_settings['HOST'], db_settings['PORT'])
    except ConnectionFailure:
        warnings.warn('MongoDB is not available. Some features may not work')
        return None, None
    else:
        db = client[db_settings['DB']]

        if 'USERNAME' in db_settings and 'PASSWORD' in db_settings:
            db.authenticate(db_settings['USERNAME'], db_settings['PASSWORD'])

        return client, db


client, db = connect()
