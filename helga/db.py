import pymongo
import warnings

from helga import settings


def _connect():
    try:
        client = pymongo.MongoClient(settings.MONGODB['HOST'], settings.MONGODB['PORT'])
    except pymongo.errors.ConnectionFailure:
        warnings.warn('MongoDB is not available. Some features may not work')
        return None, None
    else:
        db = client[settings.MONGODB['DB']]

        if 'USERNAME' in settings.MONGODB and 'PASSWORD' in settings.MONGODB:
            db.authenticate(settings.MONGODB['USERNAME'], settings.MONGODB['PASSWORD'])

        return client, db


client, db = _connect()
