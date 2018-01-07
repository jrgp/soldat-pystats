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
    return render_template('player_not_found.html', **data)

  return render_template('player.html',
                         page_title=data['player'].name,
                         **data
                         )


@app.route('/<string:server_slug>/map/<string:name>')
def _map(server_slug, name):
  try:
    server = app.config['config'].get_server(server_slug)
  except InvalidServer:
    return redirect(url_for('landing'))
  stats = Results(app.config['config'], server)

  if name is None:
      name = request.args.get('name')

  data = dict(
      map=stats.get_map(name),
  )

  data.update(more_params(stats, server))

  if not data['map']:
    return render_template('map_not_found.html', **data)

  return render_template('map.html',
                         page_title=data['map'].name,
                         **data
                         )


@app.route('/<string:server_slug>/kills', defaults=dict(startat=0))
@app.route('/<string:server_slug>/kills/pos/<int:startat>')
def latestkills(server_slug, startat):
  try:
    server = app.config['config'].get_server(server_slug)
  except InvalidServer:
    return redirect(url_for('landing'))
  stats = Results(app.config['config'], server)

  if (startat % 20):
    startat = 0

  def kill_decorate(kill):
    info = kill.__dict__
    info['killer_obj'] = stats.get_player_fields(kill.killer, ['lastcountry'])
    info['victim_obj'] = stats.get_player_fields(kill.victim, ['lastcountry'])
    info['datetime'] = pretty_datetime(datetime.utcfromtimestamp(int(info['timestamp'])))
    return info

  data = {
      'page_title': 'Latest Kills',
      'next_url': url_for('latestkills', startat=startat + 20, server_slug=server.url_slug),
      'kills': map(kill_decorate, stats.get_last_kills(startat)),
  }

  data.update(more_params(stats, server))

  if startat >= 20:
    data['prev_url'] = url_for('latestkills', startat=startat - 20, server_slug=server.url_slug)
  else:
    data['prev_url'] = False

  num_kills = stats.get_num_kills()

  if (startat + 20) > num_kills:
    data['next_url'] = False

  return render_template('latestkills.html', **data)


@app.route('/<string:server_slug>/players', defaults=dict(startat=0))
@app.route('/<string:server_slug>/players/pos/<int:startat>')
def top_players(server_slug, startat):
  try:
    server = app.config['config'].get_server(server_slug)
  except InvalidServer:
    return redirect(url_for('landing'))
  stats = Results(app.config['config'], server)

  if (startat % 20):
    startat = 0

  data = {
      'page_title': 'Top Players',
      'next_url': url_for('top_players', startat=startat + 20, server_slug=server.url_slug),
      'players': stats.get_top_killers(startat),
  }

  data.update(more_params(stats, server))

  if startat >= 20:
    data['prev_url'] = url_for('top_players', startat=startat - 20, server_slug=server.url_slug)
  else:
    data['prev_url'] = False

  num_players = stats.get_num_players()

  if (startat + 20) > num_players:
    data['next_url'] = False

  return render_template('players.html', **data)


@app.route('/<string:server_slug>/maps', defaults=dict(startat=0))
@app.route('/<string:server_slug>/maps/pos/<int:startat>')
def top_maps(server_slug, startat):
  try:
    server = app.config['config'].get_server(server_slug)
  except InvalidServer:
    return redirect(url_for('landing'))
  stats = Results(app.config['config'], server)

  if (startat % 20):
    startat = 0

  data = {
      'page_title': 'Top maps',
      'next_url': url_for('top_maps', startat=startat + 20, server_slug=server.url_slug),
      'maps': stats.get_top_maps(startat),
  }

  data.update(more_params(stats, server))

  if startat >= 20:
    data['prev_url'] = url_for('top_maps', startat=startat - 20, server_slug=server.url_slug)
  else:
    data['prev_url'] = False

  num_maps = stats.get_num_maps()

  if (startat + 20) > num_maps:
    data['next_url'] = False

  return render_template('maps.html', **data)


@app.route('/<string:server_slug>/weapons')
def weapons(server_slug):
  try:
    server = app.config['config'].get_server(server_slug)
  except InvalidServer:
    return redirect(url_for('landing'))
  stats = Results(app.config['config'], server)

  data = {
      'page_title': 'Weapons',
      'weapons': stats.get_top_weapons(),
  }

  data.update(more_params(stats, server))

  return render_template('weapons.html', **data)


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
