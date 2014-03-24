import os.path
from setuptools import setup, find_packages

version = '1.2'


requirements = []
with open(
    os.path.join(
        os.path.dirname(__file__),
        'requirements.txt',
    ),
    'r'
) as in_:
    for line in in_.readlines():
        if not line.strip() or line.startswith('#') or line.startswith('-e'):
            # Unfortunately, -e requirements can't be listed
            continue
        requirements.append(line.strip())


setup(name="helga",
      version=version,
      description=('IRC bot using twisted'),
      classifiers=[
          'Development Status :: 4 - Beta',
          'Topic :: Communications :: Chat :: Internet Relay Chat'
          'Framework :: Twisted',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      keywords='irc bot',
      author='Shaun Duncan',
      author_email='shaun.duncan@gmail.com',
      url='https://github.com/shaunduncan/helga',
      license='MIT',
      packages=find_packages(),
      install_requires=requirements,
      tests_require=[
          'freezegun',
          'mock',
          'pretend',
          'tox',
          'nose'
      ],
      test_suite='nose.collector',  # I'm not sure how to wire-up tox here :-/
      entry_points = dict(
          helga_plugins=[
              'announcements = helga.plugins.announcements:AnnouncementPlugin',
              'dubstep       = helga.plugins.dubstep:dubstep',
              'facts         = helga.plugins.facts:facts',
              'giphy         = helga.plugins.giphy:giphy',
              'help          = helga.plugins.help:help',
              'icanhazascii  = helga.plugins.icanhazascii:icanhazascii',
              'jira          = helga.plugins.jira:jira',
              'loljava       = helga.plugins.loljava:make_bullshit_java_thing',
              'manager       = helga.plugins.manager:manager',
              'meant_to_say  = helga.plugins.meant_to_say:meant_to_say',
              'no_more_olga  = helga.plugins.no_more_olga:no_more_olga',
              'oneliner      = helga.plugins.oneliner:oneliner',
              'operator      = helga.plugins.operator:operator',
              'poems         = helga.plugins.poems:poems',
              'reminders     = helga.plugins.reminders:reminders',
              'reviewboard   = helga.plugins.reviewboard:reviewboard',
              'stfu          = helga.plugins.stfu:stfu',
              'wiki_whois    = helga.plugins.wiki_whois:wiki_whois',
          ],
          console_scripts=[
              'helga = helga.run:run',
          ],
      ),
)
