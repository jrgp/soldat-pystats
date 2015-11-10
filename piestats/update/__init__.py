import redis
import os
import click
from piestats.update.kills import update_kills
from piestats.update.events import update_events
from piestats.config import PystatsConfig
from piestats.keys import PystatsKeys


@click.command()
@click.option(
    '--config_path',
    '-c',
    help='Path to config yaml file.',
    default=lambda: os.getenv('PYSTATS_CONF'),
    type=click.Path(exists=True, dir_okay=False),
    required=True)
def main(config_path):
  '''
    Run updates. Pass me path to config file which contains settings for redis
    as well as which soldat servers to process data for.
  '''

  config = PystatsConfig(config_path)
  keys = PystatsKeys(config)

  r = redis.Redis(**config.redis_connect)

  for soldat_dir in config.soldat_dirs:
    update_kills(r, keys, soldat_dir)
    update_events(r, keys, soldat_dir)
