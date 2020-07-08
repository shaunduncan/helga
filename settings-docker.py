import os


NICK = os.environ.get('HELGA_NICK', 'helga')

SERVER = {
    'TYPE': 'irc',
    'HOST': os.environ.get('HELGA_IRC_SERVER', 'localhost'),
    'PORT': 6667,
    'SSL': False,
}

CHANNELS = [
    ('#helga-dev',),
]

DATABASE = {
    'HOST': os.environ.get('HELGA_MONGO_HOST', 'mongo'),
    'PORT': 27017,
    'DB': os.environ.get('HELGA_MONGO_DB', 'helga'),
}
