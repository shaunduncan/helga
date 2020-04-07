import os


NICK = os.environ.get('HELGA_NICK', 'helga')

SERVER = {
    'HOST': os.environ.get('HELGA_IRC_SERVER'),
    'PORT': 6667,
    'SSL': False,
}

CHANNELS = [
    ('#test',),
]

DATABASE = {
    'HOST': os.environ.get('HELGA_MONGO_HOST'),
    'PORT': 27017,
    'DB': os.environ.get('HELGA_MONGO_DB', 'helga')
}
