import os
import re
import logging
from datetime import datetime, timedelta

import falcon
import redis
import ujson
from falcon import HTTPNotFound, HTTPFound
from jinja2 import FileSystemLoader
from jinja2.sandbox import SandboxedEnvironment
from babel.dates import format_datetime

from piestats.config import Config
from piestats.web.results import Results
from piestats.exceptions import InvalidServer
from piestats.status import Status
from piestats.web.helpers import PaginationHelper

ui_root = os.environ.get('STATIC_ROOT', os.path.abspath(os.path.dirname(__file__)))

jinja2_env = SandboxedEnvironment(autoescape=True)
jinja2_env.loader = FileSystemLoader(os.path.join(ui_root, 'templates'))

mimes = {'.css': 'text/css',
         '.jpg': 'image/jpeg',
         '.js': 'text/javascript',
         '.png': 'image/png',
         '.svg': 'image/svg+xml',
         '.ttf': 'application/octet-stream',
         '.woff': 'application/font-woff',
         '.ico': 'image/x-icon',
         }

_filename_ascii_strip_re = re.compile(r'[^A-Za-z0-9_.-]')


def secure_filename(filename):
    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, ' ')
    filename = str(_filename_ascii_strip_re.sub('', '_'.join(
        filename.split()))).strip('._')
    return filename


class StaticResource(object):
    allow_read_no_auth = True
    frontend_route = False

    def __init__(self, path):
        self.path = path.lstrip('/')

    def on_get(self, req, resp, filename):
        suffix = os.path.splitext(req.path)[1]
        resp.content_type = mimes.get(suffix, 'application/octet-stream')

        filepath = os.path.join(ui_root, self.path, secure_filename(filename))
        try:
            resp.stream = open(filepath, 'rb')
            resp.stream_len = os.path.getsize(filepath)
        except IOError:
            raise HTTPNotFound()


class StaticFile(object):
    allow_read_no_auth = True
    frontend_route = False

    def __init__(self, path):
        self.path = path.lstrip('/')

    def on_get(self, req, resp):
        suffix = os.path.splitext(self.path)[1]
        resp.content_type = mimes.get(suffix, 'application/octet-stream')

        filepath = os.path.join(ui_root, self.path)
        try:
            resp.stream = open(filepath, 'rb')
            resp.stream_len = os.path.getsize(filepath)
        except IOError:
            raise HTTPNotFound()


class ServerBase(object):
  def render_template(self, resp, page, response_code=None, **data):
    resp.content_type = 'text/html'
    resp.body = jinja2_env.get_template(page).render(**data)

    if response_code is not None:
        resp.status = response_code


class ServerMiddleware(object):
  def __init__(self, config):
    self.config = config

  def process_resource(self, req, resp, resource, params):
    req.context['config'] = self.config

    if not isinstance(resource, ServerBase):
      return

    server_slug = params['server']

    try:
      req.context['server'] = self.config.get_server(server_slug)
    except InvalidServer:
      resp.body = ujson.dumps({'error': 'Server not found'})
      raise HTTPNotFound()

    req.context['stats'] = Results(self.config, req.context['server'])


class Index(object):
  def on_get(self, req, resp):
    raise HTTPFound('/%s' % req.context['config'].servers[0].url_slug)


def sink_func(config):
    def inner(req, resp):
        data = {
            'servers': [],
            'since': str((datetime.now() - timedelta(days=config.data_retention)).date()),
            'timezone': str(config.timezone),
            'tojson': ujson.dumps
        }

        for server in config.ui_servers:
            results = Results(config, server)
            data['servers'].append({
                'slug': server.url_slug,
                'title': server.title,
                'num_kills': results.get_num_kills(),
                'num_players': results.get_num_players(),
            })

        ServerBase().render_template(resp, 'spa.html', **data)
    return inner


class ApiWeapons(ServerBase):
  def on_get(self, req, resp, server):
    data = {
        'data': [{'name': name, 'kills': kills} for name, kills in req.context['stats'].get_top_weapons()],
    }
    resp.body = ujson.dumps(data)


class ApiMap(ServerBase):
  def on_get(self, req, resp, server, map):
    data = {
        'data': req.context['stats'].get_map(map),
    }

    if not data['data']:
      resp.body = ujson.dumps({'error': 'Map not found'})
      raise HTTPNotFound()

    resp.body = ujson.dumps(data)


class MapSVG(ServerBase):
  def on_get(self, req, resp, server, map):
    map_info = req.context['stats'].get_map(map, get_svg=True)
    if not map_info:
        raise falcon.HTTPNotFound()
    if map_info.svg_exists:
        resp.content_type = 'image/svg+xml'
        resp.body = map_info.svg
    else:
        raise falcon.HTTPNotFound()


class ApiPlayer(ServerBase):
  def on_get(self, req, resp, server, player=None):
    if player is None:
      player = req.get_param('name', required=True)
    data = dict(
        player=req.context['stats'].get_player(player),
        top_enemies=req.context['stats'].get_player_top_enemies(player, 0, 10),
        top_victims=req.context['stats'].get_player_top_victims(player, 0, 10)
    )

    if not data['player']:
      resp.body = ujson.dumps({'error': 'Player not found'})
      raise HTTPNotFound()

    resp.body = ujson.dumps({'data': data})


class ApiKills(ServerBase):
  def on_get(self, req, resp, server, pos=0):
    pager = PaginationHelper(
        bare_route='/{server_slug}/kills'.format(server_slug=req.context['server'].url_slug),
        num_items=req.context['stats'].get_num_kills(),
        offset=pos,
        interval=20)

    def kill_decorate(kill):
      info = kill.__dict__
      info['killer_obj'] = req.context['stats'].get_player_fields_by_name(kill.killer, ['lastcountry'])
      info['victim_obj'] = req.context['stats'].get_player_fields_by_name(kill.victim, ['lastcountry'])
      info['datetime'] = int(info['timestamp'])
      info['killer_team'] = kill.killer_team
      info['victim_team'] = kill.victim_team
      return info

    data = {
        'data': [kill_decorate(kill) for kill in req.context['stats'].get_last_kills(pager.offset)],
        'total_items': pager.num_items,
    }

    resp.body = ujson.dumps(data)


class ApiMaps(ServerBase):
  def on_get(self, req, resp, server, pos=0):
    pager = PaginationHelper(
        bare_route='/{server_slug}/maps'.format(server_slug=req.context['server'].url_slug),
        num_items=req.context['stats'].get_num_maps(),
        offset=pos,
        interval=20)

    data = {
        'data': req.context['stats'].get_top_maps(pager.offset),
        'total_items': pager.num_items
    }

    resp.body = ujson.dumps(data)


class ApiRounds(ServerBase):
  def on_get(self, req, resp, server, pos=0):
    pager = PaginationHelper(
        bare_route='/{server_slug}/rounds'.format(server_slug=req.context['server'].url_slug),
        num_items=req.context['stats'].get_num_rounds(),
        offset=pos,
        interval=20)

    data = {
        'total_items': pager.num_items,
        'data': req.context['stats'].get_last_rounds(pager.offset),
    }

    resp.body = ujson.dumps(data)


class ApiRound(ServerBase):
  def on_get(self, req, resp, server, round):
    data = {
        'round': req.context['stats'].get_round(round),
    }

    if not data['round']:
      resp.body = ujson.dumps({'error': 'Round not found'})
      raise HTTPNotFound()

    def player_decorate(player):
      player['obj'] = req.context['stats'].get_player_fields(player['id'], ['lastcountry'])
      return player

    data['players'] = [player_decorate(player) for player in data['round'].players.itervalues()]

    resp.body = ujson.dumps(dict(data=data))


class ApiPlayers(ServerBase):
  def on_get(self, req, resp, server, pos=0):
    pager = PaginationHelper(
        bare_route='/{server_slug}/players'.format(server_slug=req.context['server'].url_slug),
        num_items=req.context['stats'].get_num_players(),
        offset=pos,
        interval=20)

    data = {
        'data': req.context['stats'].get_top_killers(pager.offset),
        'total_items': pager.num_items,
    }

    resp.body = ujson.dumps(data)


class ApiServer(ServerBase):
  def on_get(self, req, resp, server):
    raw_kills_per_date = req.context['stats'].get_kills_for_date_range()
    kills_per_date = zip(map(lambda d: str(format_datetime(d.date(), 'yyyy-MM-dd', tzinfo=req.context['config'].timezone)),
                             raw_kills_per_date.keys()),
                         raw_kills_per_date.values())[::-1]
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
        killsperdate=kills_per_date,
        topcountries=[
            dict(
                value=players,
                label=country,
                color=colors.pop(),
            )
            for country, players in req.context['stats'].get_top_countries(len(colors) - 1)],
        show_server_status=req.context['server'].admin_details is not None,
    )
    resp.body = ujson.dumps({'data': data})


class ApiStatus(ServerBase):
  def on_get(self, req, resp, server):
    admin_details = req.context['server'].admin_details

    if not admin_details:
      resp.body = ujson.dumps(dict(info=None, error='Admin settings not specified'))
      return

    status = Status(**admin_details)
    info = status.get_info()

    if not info:
      resp.body = ujson.dumps(dict(info=None, error='Failed getting server status'))
      return

    # Hide player IP from outside world
    for player in info['players']:
      del(player['ip'])

    info['server_slug'] = req.context['server'].url_slug

    resp.body = ujson.dumps(dict(info=info, error=None))


class ApiSearch(ServerBase):
  def on_get(self, req, resp, server):
    player_name = req.get_param('name', required=True)
    players = req.context['stats'].player_search(player_name)

    data = {
        'results': players
    }

    resp.body = ujson.dumps(data)


def init_app(config_path=None):
    if config_path is None:
        config_path = os.getenv('PYSTATS_CONF')

    logging.basicConfig(level='DEBUG')

    config = Config(config_path)
    config.redis_connection_pool = redis.ConnectionPool(**config.redis_connect)

    app = falcon.API(middleware=[ServerMiddleware(config)])

    app.add_route('/v0/{server}/map/{map}/svg', MapSVG())

    # API routes
    app.add_route('/v0/{server}/players', ApiPlayers())
    app.add_route('/v0/{server}/players/pos/{pos:int}', ApiPlayers())
    app.add_route('/v0/{server}/kills', ApiKills())
    app.add_route('/v0/{server}/kills/pos/{pos:int}', ApiKills())
    app.add_route('/v0/{server}/weapons', ApiWeapons())
    app.add_route('/v0/{server}/map/{map}', ApiMap())
    app.add_route('/v0/{server}/maps', ApiMaps())
    app.add_route('/v0/{server}/maps/pos/{pos:int}', ApiMaps())
    app.add_route('/v0/{server}/rounds', ApiRounds())
    app.add_route('/v0/{server}/rounds/pos/{pos:int}', ApiRounds())
    app.add_route('/v0/{server}/round/{round:int}', ApiRound())
    app.add_route('/v0/{server}/player/{player}', ApiPlayer())
    app.add_route('/v0/{server}/player', ApiPlayer())
    app.add_route('/v0/{server}/status', ApiStatus())
    app.add_route('/v0/{server}/search', ApiSearch())
    app.add_route('/v0/{server}', ApiServer())

    # static assets
    app.add_route('/static/{filename}', StaticResource('/static'))
    app.add_route('/static/webpack/{filename}', StaticResource('/static/webpack'))
    app.add_route('/static/soldatguns/{filename}', StaticResource('/static/soldatguns'))
    app.add_route('/static/flags/{filename}', StaticResource('/static/flags'))
    app.add_route('/static/src/{filename}', StaticResource('/static/src'))
    app.add_route('/favicon.ico', StaticFile('/static/favicon.ico'))

    # Still make home page redirect to first server
    app.add_route('/', Index())

    # Catch all to SPA
    app.add_sink(sink_func(config), '/')

    return app
