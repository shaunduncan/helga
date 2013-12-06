import pymongo
import warnings

from helga import settings


def _connect():
    db_settings = getattr(settings, 'DATABASE', {})

    try:
        client = pymongo.MongoClient(db_settings['HOST'], db_settings['PORT'])
    except pymongo.errors.ConnectionFailure:
        warnings.warn('MongoDB is not available. Some features may not work')
        return None, None
    else:
        db = client[db_settings['DB']]

        if 'USERNAME' in db_settings and 'PASSWORD' in db_settings:
            db.authenticate(db_settings['USERNAME'], db_settings['PASSWORD'])

        return client, db


client, db = _connect()
