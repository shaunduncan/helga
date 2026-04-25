import os
import subprocess
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

import helga


def parse_requirements(filename):
    with open(filename, 'r') as f:
        for line in f:
            if line.strip().startswith('#'):
                continue
            yield line


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        return subprocess.call('tox')


# Get the long description
with open(os.path.join(os.path.dirname(__file__), 'README.rst'), 'r') as f:
    long_description = f.read()


setup(name=helga.__title__,
      version=helga.__version__,
      description=helga.__description__,
      long_description=long_description,
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Topic :: Communications :: Chat :: Internet Relay Chat',
          'Framework :: Twisted',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
          'Programming Language :: Python :: 3.12',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      python_requires='>=3.7',
      keywords='helga bot irc xmpp jabber hipchat chat',
      author=helga.__author__,
      author_email='shaun.duncan@gmail.com',
      url='https://github.com/shaunduncan/helga',
      license=helga.__license__,
      packages=find_packages(),
      package_data={
          'helga': ['webhooks/logger/*.mustache'],
      },
      install_requires=list(parse_requirements('requirements.txt')),
      tests_require=[
          'freezegun',
          'mock',
          'pretend',
          'tox',
          'pytest',
      ],
      cmdclass={'test': PyTest},
      entry_points=dict(
          helga_plugins=[
              'help     = helga.plugins.help:help',
              'manager  = helga.plugins.manager:manager',
              'operator = helga.plugins.operator:operator',
              'ping     = helga.plugins.ping:ping',
              'version  = helga.plugins.version:version',
              'webhooks = helga.plugins.webhooks:WebhookPlugin',
          ],
          helga_webhooks=[
              'announcements = helga.webhooks.announcements:announce',
              'logger        = helga.webhooks.logger:logger'
          ],
          console_scripts=[
              'helga = helga.bin.helga:main',
          ],
      ),
)
