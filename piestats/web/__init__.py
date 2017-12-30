import redis
import os
from flask import Flask, render_template, url_for, redirect, request, jsonify
from piestats.config import Config
from piestats.web.results import Results
from piestats.exceptions import InvalidServer
from datetime import datetime, timedelta
from piestats.status import Status
from babel.dates import format_datetime
from collections import OrderedDict
from operator import itemgetter

app = Flask(__name__)


def init_app(config_path=None):
    if config_path is None:
        config_path = os.getenv('PYSTATS_CONF')

    config = Config(config_path)
    config.redis_connection_pool = redis.ConnectionPool(**config.redis_connect)
    app.config['config'] = config

    return app


def pretty_datetime(date):
  return format_datetime(date, tzinfo=app.config['config'].timezone)


def more_params(stats, server):
  return dict(
      footer=dict(
          num_kills=stats.get_num_kills,
          num_players=stats.get_num_players,
          since=lambda: (datetime.now() - timedelta(days=app.config['config'].data_retention)).date(),
          timezone=str(app.config['config'].timezone)
      ),
      servers=app.config['config'].servers,
      current_server=server,
      urlargs=dict(server_slug=server.url_slug),
      pretty_datetime=pretty_datetime
  )


@app.route('/<string:server_slug>/player/<path:name>')
@app.route('/<string:server_slug>/player')
def player(server_slug, name=None):
  try:
    server = app.config['config'].get_server(server_slug)
  except InvalidServer:
    return redirect(url_for('landing'))
  stats = Results(app.config['config'], server)

  if name is None:
      name = request.args.get('name')

  data = dict(
      player=stats.get_player(name),
      top_enemies=stats.get_player_top_enemies(name, 0, 10),
      top_victims=stats.get_player_top_victims(name, 0, 10)
  )

  data.update(more_params(stats, server))

  if not data['player']:
    return render_template('player_not_found.html')

  return render_template('player.html',
                         page_title=data['player'].name,
                         **data
                         )


@app.route('/<string:server_slug>/weapons/<string:weapon>')
def weapon(server_slug, weapon):
  try:
    server = app.config['config'].get_server(server_slug)
  except InvalidServer:
    return redirect(url_for('landing'))
  stats = Results(app.config['config'], server)

  info = stats.get_weapon_stats(weapon)

  if not info:
    return 'Weapon not found', 404

  data = {
      'page_title': weapon,
      'weapon': info,
  }

  data.update(more_params(stats, server))

  return render_template('weapon.html', **data)


@app.route('/<string:server_slug>/search')
def player_search(server_slug):
  try:
    server = app.config['config'].get_server(server_slug)
  except InvalidServer:
    return redirect(url_for('landing'))

  stats = Results(app.config['config'], server)

  try:
    player_name = request.args['player']
  except KeyError:
    return render_template('player_not_found.html', **more_params(stats, server))

  results = stats.player_search(player_name)

  players = []

  for player, kills in results:
    players.append(stats.get_player_fields(player, ['lastcountry', 'lastseen', 'kills']))

  if len(players) == 1:
    return redirect(url_for('player', server_slug=server_slug, name=players[0].name))

  data = {
      'page_title': 'Search results',
      'results': players,
  }

  data.update(more_params(stats, server))

  return render_template('player_search.html', **data)


@app.route('/<string:server_slug>/status')
def status(server_slug):
  try:
    server = app.config['config'].get_server(server_slug)
  except InvalidServer:
    return redirect(url_for('landing'))

  admin_details = server.admin_details

  if not admin_details:
    return jsonify(dict(success=False, info='Admin settings not specified'))

  status = Status(**admin_details)
  info = status.get_info()

  if not info:
    return jsonify(dict(success=False, info='Failed getting server status'))

  # Hide player IP from outside world
  for player in info['players']:
    del(player['ip'])

  info['server_slug'] = server_slug

  return jsonify(dict(success=True, info=info))


@app.route('/<string:server_slug>')
def index(server_slug):
  try:
    server = app.config['config'].get_server(server_slug)
  except InvalidServer:
    return redirect(url_for('landing'))
  stats = Results(app.config['config'], server)

  raw_kills_per_date = stats.get_kills_for_date_range()
  kills_per_date = OrderedDict(zip(
                               map(
                                   lambda d: str(format_datetime(d.date(), 'yyyy-MM-dd', tzinfo=app.config['config'].timezone)), raw_kills_per_date.keys()),
                               raw_kills_per_date.values()))
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
      killsperdate=kills_per_date,
      topcountries=[
          dict(
              value=players,
              label=country,
              color=colors.pop(),
          )
          for country, players in stats.get_top_countries(len(colors) - 1)],
      show_server_status=server.admin_details is not None,
      server_slug=server_slug
  )
  data.update(more_params(stats, server))
  return render_template('index.html', **data)


@app.route('/')
def landing():
  servers = app.config['config'].servers
  return redirect(url_for('index', server_slug=servers[0].url_slug))

@app.route('/v0/<string:server_slug>/players', defaults=dict(startat=0))
@app.route('/v0/<string:server_slug>/players/pos/<int:startat>')
def api_top_players(server_slug, startat):
  server = app.config['config'].get_server(server_slug)
  stats = Results(app.config['config'], server)

  if (startat % 20):
    startat = 0

  def fix_player(player):
    player['info']['lastseen'] = pretty_datetime(datetime.utcfromtimestamp(int(player['info']['lastseen'])))
    player['info']['firstseen'] = pretty_datetime(datetime.utcfromtimestamp(int(player['info']['firstseen'])))
    return player

  data = {
      'page_title': 'Top Players',
      'next_pos': startat + 20,
      'players': map(fix_player, stats.get_top_killers(startat)),
  }

  if startat >= 20:
    data['prev_pos'] = startat - 20
  else:
    data['prev_pos'] = False

  num_players = stats.get_num_players()

  if (startat + 20) > num_players:
    data['next_pos'] = False

  return jsonify(data)


@app.route('/v0/<string:server_slug>/weapons')
def api_weapons(server_slug):
  server = app.config['config'].get_server(server_slug)
  stats = Results(app.config['config'], server)
  return jsonify({
      'weapons': stats.get_top_weapons()
  })


@app.route('/v0/<string:server_slug>/kills', defaults=dict(startat=0))
@app.route('/v0/<string:server_slug>/kills/pos/<int:startat>')
def api_latestkills(server_slug, startat):
  server = app.config['config'].get_server(server_slug)
  stats = Results(app.config['config'], server)

  if (startat % 20):
    startat = 0

  def kill_decorate(kill):
    info = kill.__dict__
    info['killer_country'] = stats.get_player_fields(kill.killer, ['lastcountry']).lastcountry
    info['victim_country'] = stats.get_player_fields(kill.victim, ['lastcountry']).lastcountry
    info['date'] = pretty_datetime(datetime.utcfromtimestamp(int(info['timestamp'])))
    return info

  data = {
      'next_pos': startat + 20,
      'kills': map(kill_decorate, stats.get_last_kills(startat)),
  }

  if startat >= 20:
    data['prev_pos'] = startat=startat - 20
  else:
    data['prev_pos'] = False

  num_kills = stats.get_num_kills()

  if (startat + 20) > num_kills:
    data['next_pos'] = False

  return jsonify(data)


@app.route('/v0/<string:server_slug>/player/<string:name>')
def api_player(server_slug, name):
  server = app.config['config'].get_server(server_slug)
  stats = Results(app.config['config'], server)

  def fix_player(player):
      return player.__dict__

  data = dict(
      top_enemies=map(fix_player, stats.get_player_top_enemies(name, 0, 10)),
      top_victims=map(fix_player, stats.get_player_top_victims(name, 0, 10))
  )

  player = stats.get_player(name)
  player = player.__dict__
  player['info']['lastseen'] = pretty_datetime(datetime.utcfromtimestamp(int(player['info']['lastseen'])))
  player['info']['firstseen'] = pretty_datetime(datetime.utcfromtimestamp(int(player['info']['firstseen'])))
  player['wepstats'] = sorted(player['wepstats'].values(), key=itemgetter('kills'), reverse=True)

  data['player'] = player

  return jsonify(data)

@app.route('/spa')
def spa():
  return render_template('spa.html')
