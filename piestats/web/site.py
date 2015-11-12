import click
import os
from piestats.web import app
from piestats.config import PystatsConfig


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
    Spawn flask app. Pass me path to config file with redis connection + key
    prefix settings.
  '''

  app.config['config'] = PystatsConfig(config_path)
  app.run(host='0.0.0.0', debug=True)
