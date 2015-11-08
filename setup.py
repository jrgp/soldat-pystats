from setuptools import setup

setup(name='piestats',
      version='0.1.0',
      packages=['piestats'],
      entry_points={
          'console_scripts': [
              'runupdate = piestats.update:main',
              'runsite = piestats.web.site:main',
          ]
      }
      )
