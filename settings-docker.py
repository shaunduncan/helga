import os



NICK = os.environ.get('HELGA_NICK', 'helga')

SERVER = {
    'HOST': os.environ.get('HELGA_IRC_SERVER', 'localhost'),
    'PORT': 6667,
    'SSL': False,
    'USERNAME': os.environ.get('HELGA_IRC_USER', 'helga')
}

CHANNELS = [
    ('#test',),
]

DATABASE = {
    'HOST': os.environ.get('HELGA_MONGO_HOST', 'localhost'),
    'PORT': 27017,
    'DB': os.environ.get('HELGA_MONGO_DB', 'helga')
}
