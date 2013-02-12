import pymongo

from helga import settings


def _connect():
    client = pymongo.MongoClient(settings.MONGODB['HOST'], settings.MONGODB['PORT'])
    return client, client[settings.MONGODB['DB']]


client, db = _connect()
