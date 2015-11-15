from flask import Flask, render_template, url_for, redirect, request, jsonify
from piestats.web.results import Results
from piestats.exceptions import InvalidServer
from datetime import datetime, timedelta
from piestats.status import Status

app = Flask(__name__)


def more_params(stats, server):
  return dict(
      footer=dict(
          num_kills=stats.get_num_kills,
          num_players=stats.get_num_players,
          since=lambda: (datetime.now() - timedelta(days=app.config['config'].data_retention)).date()
      ),
      servers=app.config['config'].servers,
      current_server=server,
      urlargs=dict(server_slug=server.url_slug)
  )


@app.route('/<string:server_slug>/player/<string:name>')
def player(server_slug, name):
  try:
    server = app.config['config'].get_server(server_slug)
  except InvalidServer:
    return redirect(url_for('landing'))
  stats = Results(app.config['config'], server)

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
    info = kill._asdict()
    info['killer_obj'] = stats.get_player_fields(kill.killer, ['lastcountry'])
    info['victim_obj'] = stats.get_player_fields(kill.victim, ['lastcountry'])
    return info

  data = {
      'page_title': 'Latest Kills',
      'next_url': url_for('latestkills', startat=startat + 20, server_slug=server.url_slug),
      'kills': map(kill_decorate, stats.get_last_kills(startat)),
      'fixdate': lambda x: datetime.utcfromtimestamp(int(x))
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

  return jsonify(dict(success=True, info=info))


@app.route('/<string:server_slug>')
def index(server_slug):
  try:
    server = app.config['config'].get_server(server_slug)
  except InvalidServer:
    return redirect(url_for('landing'))
  stats = Results(app.config['config'], server)

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
      killsperdate=stats.get_kills_for_date_range(),
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
