import redis
import os
import click
import time
import logging
from piestats.update import update_events
from piestats.update.retention import Retention
from piestats.update.lock import acquire_lock
from piestats.config import Config
from piestats.keys import Keys
from piestats.web import init_app
from piestats.update.filemanager.local import LocalFileManager
from piestats.update.filemanager.ssh import SshFileManager
from piestats.update.filemanager.ftp import FtpFileManager


def get_default_config_file():
    # Maybe we're passed one via the environment
    from_env = os.getenv('PYSTATS_CONF')
    if from_env:
        return from_env

    # Or we're running this out of the git checkout and the user named
    # their conf file like this
    default_filename = 'config.yml'
    if os.path.exists(default_filename):
        return default_filename

    # Otherwise prompt for it
    return None


@click.group()
def cli():
    '''
    Piestats Soldat Stats App (https://github.com/jrgp/soldat-pystats)
    '''


@cli.command()
@click.option(
    '--config_path',
    '-c',
    help='Path to config yaml file.',
    default=get_default_config_file,
    type=click.Path(exists=True, dir_okay=False),
    required=True)
@click.option(
    '--verbose',
    '-v',
    help='Show HWID mismatches',
    is_flag=True)
def update(config_path, verbose):
  '''
    Run updates. Pass me path to config file which contains settings for redis
    as well as which soldat servers to process data for.
  '''

  with acquire_lock():

    start = time.time()
    # Parse our config yaml file
    config = Config(config_path)

    r = redis.Redis(**config.redis_connect)

    for server in config.servers:
      print('Updating stats for {server.url_slug} ({server.title}) ({server.log_source})'.format(server=server))

      # Redis key name manager
      keys = Keys(config, server)

      # Limit our data to however much retention
      retention = Retention(r, keys, config, server)

      # Parse each of our soldat DIRs
      for soldat_dir in server.dirs:

        # Support getting logs via local files or ssh or ftp
        if server.log_source == 'local':
          filemanager = LocalFileManager(r, keys, soldat_dir, retention)
        elif server.log_source == 'ssh':
          filemanager = SshFileManager(r, keys, soldat_dir, retention, server.connection_options)
        elif server.log_source == 'ftp':
          filemanager = FtpFileManager(r, keys, soldat_dir, retention, server.connection_options)

        # Console logs
        try:
            update_events(r, keys, retention, filemanager, server, verbose)
        except Exception:
            logging.exception('Failed updating stats for %s (%s) (%s)', server.url_slug, server.title, server.log_source)

      # Trim old events
      retention.run_retention()
      print('Updating took {0} seconds'.format(round(time.time() - start, 2)))


@cli.command()
@click.option(
    '--config_path',
    '-c',
    help='Path to config yaml file.',
    default=get_default_config_file,
    type=click.Path(exists=True, dir_okay=False),
    required=True)
def web(config_path):
  '''
    Serve website. Pass me path to config file with redis connection + key
    prefix settings.
  '''

  config = Config(config_path)

  from gunicorn.app.base import BaseApplication

  # Boilerplate for running gunicorn from within python instead of via
  # an external command
  class App(BaseApplication):
    def __init__(self, config={}):
      self.options = config
      super(App, self).__init__()

    def load_config(self):
      for key, value in self.options.items():
        if key in self.cfg.settings and value is not None:
          self.cfg.set(key.lower(), value)

    def load(self):
      app = init_app(config_path)
      return app

  # Default run options
  run_options = {
      'bind': '0:5000',
      'workers': 4,
      'worker_class': 'gevent',
      'accesslog': '-',
  }

  # Override with ones that might exist in config
  run_options.update(config.gunicorn_settings)

  # Start the embedded gunicorn
  g_server = App(run_options)
  g_server.run()


if __name__ == '__main__':
  cli()
