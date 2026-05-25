import os

# Load .env file from current working directory (if present)
_env_file = os.path.join(os.getcwd(), ".env")
if os.path.isfile(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())

NICK = os.environ.get("HELGA_NICK", "helga")

server_type = os.environ.get("HELGA_SERVER_TYPE", "irc")

if server_type == "discord":
    SERVER = {
        "TYPE": "discord",
        "TOKEN": os.environ["HELGA_DISCORD_TOKEN"],
    }
else:
    SERVER = {
        "TYPE": server_type,
        "HOST": os.environ.get("HELGA_IRC_SERVER", "localhost"),
        "PORT": 6667,
        "SSL": False,
    }

channels_env = os.environ.get("HELGA_CHANNELS", "#helga-dev")
CHANNELS = [(c.strip(),) for c in channels_env.split(",") if c.strip()]

DATABASE = {
    "HOST": os.environ.get("HELGA_MONGO_HOST", "localhost"),
    "PORT": 27017,
    "DB": os.environ.get("HELGA_MONGO_DB", "helga"),
}

# Made with Bob
