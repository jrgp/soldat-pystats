from flask import Flask, render_template, url_for
from piestats.results import stats
from piestats.config import PystatsConfig
from datetime import datetime, timedelta
import click
import os

app = Flask(__name__)


@app.context_processor
def more_context():
  s = stats(app.config['config'])
  return dict(
      footer=dict(
          num_kills=s.get_num_kills(),
          num_players=s.get_num_players(),
          since=(datetime.now() - timedelta(days=app.config['config'].data_retention)).date()
      )
  )


@app.route('/player/<string:name>')
def player(name):
  player = stats(app.config['config']).get_player(name)
  if not player:
    return render_template('player_not_found.html')
  return render_template('player.html', page_title=player.name, player=player)


@app.route('/kills', defaults=dict(startat=0))
@app.route('/kills/pos/<int:startat>')
def latestkills(startat):
  s = stats(app.config['config'])

  if (startat % 20):
    startat = 0

  def kill_decorate(kill):
    info = kill._asdict()
    info['killer_obj'] = s.get_player_fields(kill.killer, ['lastcountry'])
    info['victim_obj'] = s.get_player_fields(kill.victim, ['lastcountry'])
    return info

  data = {
      'page_title': 'Latest Kills',
      'next_url': url_for('latestkills', startat=startat + 20),
      'kills': map(kill_decorate, s.get_last_kills(startat)),
      'fixdate': lambda x: datetime.utcfromtimestamp(int(x))
  }

  if startat >= 20:
    data['prev_url'] = url_for('latestkills', startat=startat - 20)
  else:
    data['prev_url'] = False

  return render_template('latestkills.html', **data)


@app.route('/players', defaults=dict(startat=0))
@app.route('/players/pos/<int:startat>')
def top_players(startat):
  s = stats(app.config['config'])

  if (startat % 20):
    startat = 0

  data = {
      'page_title': 'Top Players',
      'next_url': url_for('top_players', startat=startat + 20),
      'players': s.get_top_killers(startat),
  }

  if startat >= 20:
    data['prev_url'] = url_for('top_players', startat=startat - 20)
  else:
    data['prev_url'] = False

  return render_template('players.html', **data)


@app.route('/weapons')
def weapons():
  s = stats(app.config['config'])

  data = {
      'page_title': 'Weapons',
      'weapons': s.get_top_weapons(),
  }

  return render_template('weapons.html', **data)


@app.route('/')
def index():
  s = stats(app.config['config'])
  colors = [
      'red',
      'blue',
      'green',
      'orange',
      'pink',
      'brown',
      'purple',
  ]
  data = dict(
      page_title='Stats overview',
      killsperdate=s.get_kills_for_date_range(),
      topcountries=[
          dict(
              value=players,
              label=country,
              color=colors.pop(),
          )
          for country, players in s.get_top_countries(len(colors) - 1)]
  )
  return render_template('index.html', **data)


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
