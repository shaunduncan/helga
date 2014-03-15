from setuptools import setup, find_packages

version = '1.3'

setup(name="helga",
      version=version,
      description=('IRC bot using twisted'),
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: IRC',
                   'Intended Audience :: Twisted Developers, IRC Bot Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Software Development :: Libraries :: Python Modules',
                   'Topic :: IRC Bots'],
      keywords='irc bot',
      author='Shaun Duncan',
      author_email='shaun.duncan@gmail.com',
      url='https://github.com/shaunduncan/helga',
      license='MIT',
      packages=find_packages(),
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
