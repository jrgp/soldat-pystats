import redis
import os
import click
from piestats.update import update_kills
from piestats.update.events import update_events
from piestats.update.retention import Retention
from piestats.config import Config
from piestats.keys import Keys
from piestats.web import app


@click.command()
@click.option(
    '--config_path',
    '-c',
    help='Path to config yaml file.',
    default=lambda: os.getenv('PYSTATS_CONF'),
    type=click.Path(exists=True, dir_okay=False),
    required=True)
def run_update(config_path):
  '''
    Run updates. Pass me path to config file which contains settings for redis
    as well as which soldat servers to process data for.
  '''

  config = Config(config_path)

  r = redis.Redis(**config.redis_connect)

  for server in config.servers:
    print('Updating stats for {server}'.format(server=server.url_slug))
    keys = Keys(config, server)
    retention = Retention(r, keys, config)
    for soldat_dir in server.dirs:
      update_kills(r, keys, retention, soldat_dir)
      update_events(r, keys, soldat_dir)
    retention.run_retention()


@click.command()
@click.option(
    '--config_path',
    '-c',
    help='Path to config yaml file.',
    default=lambda: os.getenv('PYSTATS_CONF'),
    type=click.Path(exists=True, dir_okay=False),
    required=True)
def run_site(config_path):
  '''
    Spawn flask app. Pass me path to config file with redis connection + key
    prefix settings.
  '''

  config = Config(config_path)
  app.config['config'] = config
  app.run(**config.flask_run)
