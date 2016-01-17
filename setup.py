from setuptools import setup, find_packages

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
      install_requires=[
          'click==5.1',
          'flake8==2.5.0',
          'Flask==0.10.1',
          'itsdangerous==0.24',
          'Jinja2==2.8',
          'MarkupSafe==0.23',
          'mccabe==0.3.1',
          'pep8==1.5.7',
          'pyflakes==1.0.0',
          'python-dateutil==2.4.2',
          'python-geoip==1.2',
          'python-geoip-geolite2==2015.303',
          'PyYAML==3.11',
          'redis==2.10.5',
          'six==1.10.0',
          'Werkzeug==0.10.4',
          'IPy==0.83',
      ]
      )
