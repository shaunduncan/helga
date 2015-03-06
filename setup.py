import functools
import pkg_resources
import subprocess
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

from pip.req import parse_requirements as parse_reqs

import helga


# Compatibility with older versions of pip
pip_dist = pkg_resources.get_distribution('pip')
pip_version = tuple(map(int, pip_dist.version.split('.')))

# Use a base partial that will be updated depending on the version of pip
parse_requirements = functools.partial(parse_reqs, options=None)

if pip_version < (1, 2):
    # pip versions before 1.2 require an options keyword for using it outside
    # of invoking a pip shell command
    from pip.baseparser import parser
    parse_requirements.keywords['options'] = parser.parse_args()[0]

if pip_version >= (1, 5):
    # pip 1.5 introduced a session kwarg that is required in later versions
    from pip.download import PipSession
    parse_requirements.keywords['session'] = PipSession()


# If installing on python 2.6, we need to install the argparse backport
extra_requires = []
if sys.version_info[:2] == (2, 6):
    extra_requires = ['argparse==1.3.0']


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        return subprocess.call('tox')


setup(name=helga.__title__,
      version=helga.__version__,
      description=helga.__description__,
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Topic :: Communications :: Chat :: Internet Relay Chat',
          'Framework :: Twisted',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      keywords='helga bot irc xmpp jabber hipchat chat',
      author=helga.__author__,
      author_email='shaun.duncan@gmail.com',
      url='https://github.com/shaunduncan/helga',
      license=helga.__license__,
      packages=find_packages(),
      package_data={
          'helga': ['webhooks/logger/*.mustache'],
      },
      install_requires=[
          str(req.req) for req in parse_requirements('requirements.txt')
      ] + extra_requires,
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
