import os

from setuptools import find_packages, setup


def parse_requirements(filename):
    """Parse requirements from a requirements file."""
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                yield line


def get_version():
    """Get version from helga/__init__.py without importing it."""
    version_file = os.path.join(os.path.dirname(__file__), "helga", "__init__.py")
    with open(version_file) as f:
        for line in f:
            if line.startswith("__version__"):
                # Extract version string
                return line.split("=")[1].strip().strip("'\"")
    raise RuntimeError("Unable to find version string.")


def get_long_description():
    """Get the long description from README.rst."""
    readme_path = os.path.join(os.path.dirname(__file__), "README.rst")
    with open(readme_path) as f:
        return f.read()


# For backward compatibility, setup.py still works
# but pyproject.toml is now the primary configuration
setup(
    name="helga",
    version=get_version(),
    description="A full-featured chat bot for Python 3.8+ with plugin support",
    long_description=get_long_description(),
    long_description_content_type="text/x-rst",
    author="Shaun Duncan",
    author_email="shaun.duncan@gmail.com",
    url="https://github.com/shaunduncan/helga",
    license="MIT OR GPL-3.0-or-later",
    packages=find_packages(),
    package_data={
        "helga": ["webhooks/logger/*.mustache"],
    },
    install_requires=list(parse_requirements("requirements.txt")),
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Communications :: Chat :: Internet Relay Chat",
        "Framework :: Twisted",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="helga bot irc xmpp jabber hipchat chat slack discord",
    entry_points={
        "helga_plugins": [
            "help = helga.plugins.help:help",
            "manager = helga.plugins.manager:manager",
            "operator = helga.plugins.operator:operator",
            "ping = helga.plugins.ping:ping",
            "version = helga.plugins.version:version",
            "webhooks = helga.plugins.webhooks:WebhookPlugin",
        ],
        "helga_webhooks": [
            "announcements = helga.webhooks.announcements:announce",
            "logger = helga.webhooks.logger:logger",
        ],
        "console_scripts": [
            "helga = helga.bin.helga:main",
        ],
    },
)

# Made with Bob
