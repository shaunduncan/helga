import pymongo

from helga import settings


def _connect():
    try:
        client = pymongo.MongoClient(settings.MONGODB['HOST'], settings.MONGODB['PORT'])
    except pymongo.errors.ConnectionFailure:
        return None, None
    else:
        return client, client[settings.MONGODB['DB']]


client, db = _connect()
