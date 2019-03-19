import os
from setuptools import setup, find_packages


# Try to get the contents of our requirements.txt file. This is to avoid
# needing to maintain a separate list of install deps in this file
def get_runtime_deps():
    filename = 'requirements.txt'

    potential_paths = [
        # Should work if running `python setup.py whatever` within the source folder
        os.path.join(os.path.dirname(os.path.realpath(__file__)), filename),

        # These hacks should make pex work
        os.path.join(os.environ.get('PWD', ''), filename),
        os.path.join(os.path.dirname(os.environ.get('VIRTUAL_ENV', '')), filename),
    ]

    for path in potential_paths:
        try:
            with open(path) as h:
                return [line.strip() for line in h if line.strip() != '']
        except IOError:
            continue

    return []


setup(name='piestats',
      version='0.1.0',
      packages=find_packages(),
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'runupdate = piestats.cli:update',
              'runsite = piestats.cli:web',

              # Compilation of above two commands in one
              'piestats = piestats.cli:cli',
          ]
      },
      install_requires=get_runtime_deps(),
      extras_require={
          'dev': [
              'pytest',
              'pytest-cov',
              'flake8',
          ]
      }
      )
