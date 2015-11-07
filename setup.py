from setuptools import setup

setup(name='piestats',
  version='0.1.0',
  packages=['piestats'],
  entry_points={
    'console_scripts': [
      'update = piestats.update:main',
      'runsite = piestats.web.site:main',
    ]
  }
)
