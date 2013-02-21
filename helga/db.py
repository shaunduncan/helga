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
        return client, client[settings.MONGODB['DB']]


client, db = _connect()
