import os
import re
import logging
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta

import falcon
import redis
import ujson
from falcon import HTTPNotFound, HTTPFound, HTTP_404
from jinja2 import FileSystemLoader
from jinja2.sandbox import SandboxedEnvironment
from babel.dates import format_datetime

from piestats.config import Config
from piestats.web.results import Results
from piestats.exceptions import InvalidServer
from piestats.status import Status
from piestats.web.pager import PaginationHelper
from piestats.compat import sanitize_for_json

ui_root = os.environ.get('STATIC_ROOT', os.path.abspath(os.path.dirname(__file__)))

jinja2_env = SandboxedEnvironment(autoescape=True)
jinja2_env.loader = FileSystemLoader(os.path.join(ui_root, 'templates'))

mimes = {'.css': 'text/css',
         '.jpg': 'image/jpeg',
         '.js': 'text/javascript',
         '.png': 'image/png',
         '.svg': 'image/svg+xml',
         '.ttf': 'application/octet-stream',
         '.woff': 'application/font-woff'}

_filename_ascii_strip_re = re.compile(r'[^A-Za-z0-9_.-]')
_safe_username_re = re.compile(r'^[^.][a-zA-Z0-9-\. ]+$')


def secure_filename(filename):
    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, ' ')
    filename = str(_filename_ascii_strip_re.sub('', '_'.join(
        filename.split()))).strip('._')
    return filename


def pretty_duration(source_seconds):
  hours, remainder = divmod(source_seconds, 3600)
  minutes, seconds = divmod(remainder, 60)
  resp = []

  if hours:
    resp.append('%dh' % hours)

  if minutes:
    resp.append('%dm' % minutes)

  if seconds:
    resp.append('%ds' % seconds)

  return ''.join(resp)


def pretty_datetime(timezone):
  return lambda date: format_datetime(date, tzinfo=timezone)


def bad_username(username):
  return not _safe_username_re.match(username)


def player_url(server, username):
  if not username:
    return None
  if bad_username(username):
    return '/{server}/player?name={username}'.format(server=server, username=urllib.parse.quote_plus(username))
  else:
    return '/{server}/player/{username}'.format(server=server, username=username)


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
            resp.content_length = os.path.getsize(filepath)
        except IOError:
            raise HTTPNotFound()


class ServerBase(object):
  def more_data(self, req):
    return dict(
        footer=dict(
            num_kills=req.context['stats'].get_num_kills,
            num_players=req.context['stats'].get_num_players,
            since=lambda: (datetime.now() - timedelta(days=req.context['config'].data_retention)).date(),
            timezone=str(req.context['config'].timezone)
        ),
        servers=req.context['config'].ui_servers,
        current_server=req.context['server'],
        server_slug=req.context['server'].url_slug,
        urlargs=dict(server_slug=req.context['server'].url_slug, player_url=player_url),
        pretty_datetime=pretty_datetime(req.context['config'].timezone),
        enumerate=enumerate,
        len=len,
        pretty_duration=pretty_duration,
        req=req
    )

  def render_template(self, req, resp, page, response_code=None, **data):
    # Add json support to essentially all routes
    if req.context['do_json']:
        if response_code == HTTP_404:
            raise falcon.HTTPNotFound()
        else:
            # Remove stuff not useful for json
            data.pop('page_title', None)

            # Give it
            resp.body = ujson.dumps(sanitize_for_json(data))
            return

    # Add stuff needed for displaying the template
    data.update(self.more_data(req))

    resp.content_type = 'text/html'
    resp.body = jinja2_env.get_template(page).render(**data)

    if response_code is not None:
        resp.status = response_code


class ServerMiddleware(object):
  def __init__(self, config):
    self.config = config

  def process_resource(self, req, resp, resource, params):
    req.context['do_json'] = req.get_param('json') is not None or req.get_header('Accept') == 'application/json'
    req.context['config'] = self.config

    if not isinstance(resource, ServerBase):
      return

    server_slug = params['server']

    try:
      req.context['server'] = self.config.get_server(server_slug)
    except InvalidServer:
      raise HTTPFound('/')

    req.context['stats'] = Results(self.config, req.context['server'])


class Index(object):
  def on_get(self, req, resp):
    raise HTTPFound('/%s' % req.context['config'].servers[0].url_slug)


class Weapons(ServerBase):
  def on_get(self, req, resp, server):
    data = {
        'page_title': 'Weapons',
        'weapons': req.context['stats'].get_top_weapons(),
    }
    self.render_template(req, resp, 'weapons.html', **data)


class Map(ServerBase):
  def on_get(self, req, resp, server, map):
    data = {
        'page_title': 'Map %s' % map,
        'map': req.context['stats'].get_map(map),
    }

    if not data['map']:
      self.render_template(req, resp, 'map_not_found.html', response_code=HTTP_404, **data)
      return

    self.render_template(req, resp, 'map.html', **data)


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


class Player(ServerBase):
  def on_get(self, req, resp, server, player=None):
    if player is None:
      player = req.get_param('name', required=True)
    data = dict(
        player=req.context['stats'].get_player(player),
        top_enemies=req.context['stats'].get_player_top_enemies(player, 0, 10),
        top_victims=req.context['stats'].get_player_top_victims(player, 0, 10)
    )

    if not data['player']:
      self.render_template(req, resp, 'player_not_found.html', response_code=HTTP_404, **data)
      return

    self.render_template(req, resp, 'player.html',
                         page_title=data['player'].name,
                         **data)


class Kills(ServerBase):
  def on_get(self, req, resp, server, pos=0):
    pager = PaginationHelper(
        bare_route='/{server_slug}/kills'.format(server_slug=req.context['server'].url_slug),
        num_items=req.context['stats'].get_num_kills(),
        offset=pos,
        interval=20)

    data = {
        'page_title': 'Latest Kills',
        'next_url': pager.next_url,
        'prev_url': pager.prev_url,
    }

    def kill_decorate(kill):
      info = kill.__dict__
      info['killer_obj'] = req.context['stats'].get_player_fields_by_name(kill.killer, ['lastcountry'])
      info['victim_obj'] = req.context['stats'].get_player_fields_by_name(kill.victim, ['lastcountry'])
      info['killer_team'] = kill.killer_team
      info['victim_team'] = kill.victim_team
      return info

    data['kills'] = (kill_decorate(kill) for kill in req.context['stats'].get_last_kills(pager.offset))

    self.render_template(req, resp, 'latestkills.html', **data)


class Maps(ServerBase):
  def on_get(self, req, resp, server, pos=0):
    pager = PaginationHelper(
        bare_route='/{server_slug}/maps'.format(server_slug=req.context['server'].url_slug),
        num_items=req.context['stats'].get_num_maps(),
        offset=pos,
        interval=20)

    data = {
        'page_title': 'Top maps',
        'next_url': pager.next_url,
        'prev_url': pager.prev_url,
        'maps': req.context['stats'].get_top_maps(pager.offset),
    }

    self.render_template(req, resp, 'maps.html', **data)


class Rounds(ServerBase):
  def on_get(self, req, resp, server, pos=0):
    pager = PaginationHelper(
        bare_route='/{server_slug}/rounds'.format(server_slug=req.context['server'].url_slug),
        num_items=req.context['stats'].get_num_rounds(),
        offset=pos,
        interval=20)

    data = {
        'page_title': 'Latest Rounds',
        'next_url': pager.next_url,
        'prev_url': pager.prev_url,
        'rounds': req.context['stats'].get_last_rounds(pager.offset),
    }

    self.render_template(req, resp, 'lastrounds.html', **data)


class Round(ServerBase):
  def on_get(self, req, resp, server, round):
    data = {
        'page_title': 'Round %s' % round,
        'round': req.context['stats'].get_round(round),
    }

    if not data['round']:
      self.render_template(req, resp, 'not_found.html', item='round', **data)
      return

    self.render_template(req, resp, 'round.html', **data)


class Players(ServerBase):
  def on_get(self, req, resp, server, pos=0):
    pager = PaginationHelper(
        bare_route='/{server_slug}/players'.format(server_slug=req.context['server'].url_slug),
        num_items=req.context['stats'].get_num_players(),
        offset=pos,
        interval=20)

    data = {
        'page_title': 'Top Players',
        'next_url': pager.next_url,
        'prev_url': pager.prev_url,
        'players': req.context['stats'].get_top_killers(pager.offset),
    }

    self.render_template(req, resp, 'players.html', **data)


class Server(ServerBase):
  def on_get(self, req, resp, server):
    raw_kills_per_date = req.context['stats'].get_kills_for_date_range()
    kills_per_date_keys = [str(format_datetime(d.date(), 'yyyy-MM-dd', tzinfo=req.context['config'].timezone)) for d in list(raw_kills_per_date.keys())]
    kills_per_date_values = list(raw_kills_per_date.values())
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
        kills_per_date_keys=kills_per_date_keys,
        kills_per_date_values=kills_per_date_values,
        topcountries=[
            dict(
                value=players,
                label=country,
                color=colors.pop(),
            )
            for country, players in req.context['stats'].get_top_countries(len(colors) - 1)],
        show_server_status=req.context['server'].admin_details is not None,
        server_slug=req.context['server'].url_slug,
    )
    self.render_template(req, resp, 'index.html', **data)


class StatusRoute(ServerBase):
  def on_get(self, req, resp, server):
    admin_details = req.context['server'].admin_details

    if not admin_details:
      resp.body = ujson.dumps(dict(success=False, info='Admin settings not specified'))
      return

    status = Status(**admin_details)
    info = status.get_info()

    if not info:
      resp.body = ujson.dumps(dict(success=False, info='Failed getting server status'))
      return

    # Hide player IP from outside world
    for player in info['players']:
      del(player['ip'])

    info['server_slug'] = req.context['server'].url_slug

    resp.body = ujson.dumps(dict(success=True, info=info))


class Search(ServerBase):
  def on_get(self, req, resp, server):
    player_name = req.get_param('player')
    if not player_name:
      self.render_template(req, resp, 'player_not_found.html', **self.more_data(req))
      return

    players = req.context['stats'].player_search(player_name)

    if len(players) == 1:
      raise HTTPFound(player_url(req.context['server'].url_slug, players[0].name))

    data = {
        'page_title': 'Search results',
        'results': players,
    }

    self.render_template(req, resp, 'player_search.html', **data)


def init_app(config_path=None):
    if config_path is None:
        config_path = os.getenv('PYSTATS_CONF')

    logging.basicConfig(level='DEBUG')

    config = Config(config_path)
    config.redis_connection_pool = redis.ConnectionPool(**config.redis_connect)

    app = falcon.API(middleware=[ServerMiddleware(config)])

    app.add_route('/{server}/player/{player}', Player())
    app.add_route('/{server}/player', Player())

    app.add_route('/{server}/players', Players())
    app.add_route('/{server}/players/pos/{pos:int}', Players())

    app.add_route('/{server}/map/{map}', Map())
    app.add_route('/{server}/map/{map}/svg', MapSVG())
    app.add_route('/{server}/maps', Maps())
    app.add_route('/{server}/maps/pos/{pos:int}', Maps())

    app.add_route('/{server}/round/{round}', Round())
    app.add_route('/{server}/rounds', Rounds())
    app.add_route('/{server}/rounds/pos/{pos:int}', Rounds())

    app.add_route('/{server}/kills', Kills())
    app.add_route('/{server}/kills/pos/{pos:int}', Kills())

    app.add_route('/{server}/weapons', Weapons())

    app.add_route('/{server}/search', Search())

    app.add_route('/{server}/status', StatusRoute())

    app.add_route('/{server}', Server())
    app.add_route('/', Index())

    app.add_route('/static/{filename}', StaticResource('/static'))
    app.add_route('/static/soldatguns/{filename}', StaticResource('/static/soldatguns'))
    app.add_route('/static/flags/{filename}', StaticResource('/static/flags'))

    return app
