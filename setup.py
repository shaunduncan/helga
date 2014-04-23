from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import subprocess

from pip.req import parse_requirements

version = '1.4.5'


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        return subprocess.call('tox')


setup(name="helga",
      version=version,
      description=('IRC bot using twisted that supports plugins'),
      classifiers=[
          'Development Status :: 4 - Beta',
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
      keywords='irc bot helga',
      author='Shaun Duncan',
      author_email='shaun.duncan@gmail.com',
      url='https://github.com/shaunduncan/helga',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          str(req.req) for req in parse_requirements('requirements.txt')
      ],
      tests_require=[
          'freezegun',
          'mock',
          'pretend',
          'tox',
          'pytest',
      ],
      cmdclass = {'test': PyTest},
      entry_points = dict(
          helga_plugins=[
              'dubstep      = helga.plugins.dubstep:dubstep',
              'facts        = helga.plugins.facts:facts',
              'giphy        = helga.plugins.giphy:giphy',
              'help         = helga.plugins.help:help',
              'icanhazascii = helga.plugins.icanhazascii:icanhazascii',
              'jira         = helga.plugins.jira:jira',
              'loljava      = helga.plugins.loljava:make_bullshit_java_thing',
              'manager      = helga.plugins.manager:manager',
              'meant_to_say = helga.plugins.meant_to_say:meant_to_say',
              'no_more_olga = helga.plugins.no_more_olga:no_more_olga',
              'oneliner     = helga.plugins.oneliner:oneliner',
              'operator     = helga.plugins.operator:operator',
              'poems        = helga.plugins.poems:poems',
              'reminders    = helga.plugins.reminders:reminders',
              'reviewboard  = helga.plugins.reviewboard:reviewboard',
              'stfu         = helga.plugins.stfu:stfu',
              'webhooks     = helga.plugins.webhooks:WebhookPlugin',
              'wiki_whois   = helga.plugins.wiki_whois:wiki_whois',
          ],
          helga_webhooks=[
              'announcements = helga.webhooks.announcements:announce'
          ],
          console_scripts=[
              'helga = helga.run:run',
          ],
      ),
)
