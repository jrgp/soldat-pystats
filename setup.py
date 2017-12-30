import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'requirements.txt')) as h:
    deps = [line.strip() for line in h if line.strip() != '']

setup(name='piestats',
      version='0.1.0',
      packages=find_packages(),
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'runupdate = piestats.cli:run_update',
              'runsite = piestats.cli:run_site',
          ]
      },
      install_requires=deps
      )
