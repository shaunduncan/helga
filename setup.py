from setuptools import setup, find_packages

version = '0.0.1'

setup(name="helga",
      version=version,
      description=('IRC bot using twisted'),
      classifiers=['Development Status :: 1 - Beta',
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
      entry_points={
          'console_scripts': [
              'helga = helga.run:run'
          ]
      })
