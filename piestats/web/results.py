import operator
import redis
from datetime import datetime, timedelta
from collections import OrderedDict
from piestats.keys import Keys
from piestats.models.player import Player
from piestats.models.map import Map
from piestats.models.kill import Kill
from piestats.models.round import Round
from piestats.web.helpers import remove_redundant_player_names


class Results():
  ''' Abstraction used to scrape redis to provide details to web app '''
  def __init__(self, config, server):
    self.r = redis.Redis(connection_pool=config.redis_connection_pool)
    self.keys = Keys(config, server)
    self.server = server

  def get_num_kills(self):
    try:
      return self.r.zcard(self.keys.kill_log)
    except ValueError:
      return 0

  def get_num_players(self):
    ''' number of players with kills we have '''
    try:
      return int(self.r.zcard(self.keys.top_players))
    except ValueError:
      return 0

  def get_num_maps(self):
    ''' number of maps we have '''
    try:
      return int(self.r.zcard(self.keys.top_maps))
    except ValueError:
      return 0

  def get_num_rounds(self):
    ''' number of rounds we have '''
    try:
      return self.r.zcard(self.keys.round_log)
    except ValueError:
      return 0

  def get_top_killers(self, startat=0, incr=20):
    ''' list of Player objects sorted by those with the most kills desc '''
    results = self.r.zrevrange(self.keys.top_players, startat, startat + incr, withscores=True)
    for player_id, kills in results:
      more = self.hmget_with_keys(self.keys.player_hash(player_id), ['deaths', 'lastseen', 'firstseen', 'lastcountry', 'scores:Alpha', 'scores:Bravo'])
      yield Player(name=self.get_name_from_id(player_id),
                   kills=kills,
                   **more
                   )

  def get_top_maps(self, startat=0, incr=20):
    ''' list of Map objects sorted by those with the most plays desc '''
    results = self.r.zrevrange(self.keys.top_maps, startat, startat + incr, withscores=True)
    for name, plays in results:
      more = self.hmget_with_keys(self.keys.map_hash(name), ['scores:Alpha', 'scores:Bravo', 'wins:bravo', 'wins:alpha', 'kills', 'flags'])
      yield Map(name=name,
                plays=plays,
                **more
                )

  def get_player(self, _player):
    ''' given a player id, get a Player object '''
    _player_id = self.get_id_from_name(_player)
    if not _player_id:
      return None
    info = self.r.hgetall(self.keys.player_hash(_player_id))
    if not info:
      return None
    info['names'] = self.get_all_names_from_id(_player_id)
    return Player(name=self.get_name_from_id(_player_id), **info)

  def get_round(self, _round):
    ''' given a round id, get a Round object '''
    info = self.r.hgetall(self.keys.round_hash(_round))
    if not info:
      return None
    return Round(round_id=_round, **info).resolve_player_ids(self.get_name_from_id)

  def get_map(self, _map, get_svg=False):
    ''' given a map name, get a Map object '''
    # Manually get list of all keys we have for this map, so
    # if we don't want to get the gigantic svg xml blob, we
    # can selectively remove it
    keys = self.r.hkeys(self.keys.map_hash(_map))

    # No keys returned? Map doesn't exist
    if not keys:
      return None

    keys = set(keys)
    has_svg = 'svg_image' in keys

    if not get_svg:
      keys.discard('svg_image')

    keys = list(keys)

    info = self.hmget_with_keys(self.keys.map_hash(_map), keys)

    if not info:
      return None

    # Make sure the svg_exists property on the map model
    # will continue to work if we do in fact have the svg
    # but are not retrieving it, by setting its key to None
    if not get_svg and has_svg:
      info['svg_image'] = None

    info['plays'] = self.r.zscore(self.keys.top_maps, _map) or 0
    return Map(name=_map, **info)

  def get_player_fields_by_name(self, player_name, fields=[]):
    ''' given a player name and some keys, get back a populated Player object '''
    player_id = self.get_id_from_name(player_name)
    if not player_id:
      return
    return self.get_player_fields(player_id, fields)

  def get_player_fields(self, _player_id, fields=[]):
    ''' given a player id and some keys, get back a populated Player object '''
    info = {}
    for key in fields:
      info[key] = self.r.hget(self.keys.player_hash(_player_id), key)
    return Player(name=self.get_name_from_id(_player_id), **info)

  def get_player_top_enemies(self, _player, startat=0, incr=20):
    ''' given a player name, get list of Player objects for that player, sorted by number of times they killed us desc '''
    _player_id = self.get_id_from_name(_player)
    if not _player_id:
      return
    results = self.r.zrevrange(self.keys.player_top_enemies(_player_id), 0, startat + incr, withscores=True)
    for enemy_id, their_kills in results:
      more = self.hmget_with_keys(self.keys.player_hash(enemy_id), ['lastcountry'])
      my_deaths = float(self.r.zscore(self.keys.player_top_enemies(enemy_id), _player_id) or 0)
      more['kd'] = '%.2f' % (their_kills / my_deaths if my_deaths > 0 else 0)
      yield Player(name=self.get_name_from_id(enemy_id),
                   kills=their_kills,
                   **more
                   )

  def get_player_top_victims(self, _player, startat=0, incr=20):
    ''' given a player name, get list of Player objects for that player, sorted by number of times we killed them us desc '''
    _player_id = self.get_id_from_name(_player)
    if not _player_id:
      return
    results = self.r.zrevrange(self.keys.player_top_victims(_player_id), 0, startat + incr, withscores=True)
    for victim_id, my_kills in results:
      more = self.hmget_with_keys(self.keys.player_hash(victim_id), ['lastcountry'])
      their_deaths = float(self.r.zscore(self.keys.player_top_victims(victim_id), _player_id) or 0)
      more['kd'] = '%.2f' % (my_kills / their_deaths if their_deaths > 0 else 0)
      yield Player(name=self.get_name_from_id(victim_id),
                   kills=my_kills,
                   **more
                   )

  def get_last_kills(self, startat=0, incr=20):
    ''' given pagination, get list of most recent Kill objects '''
    kill_ids = self.r.zrevrange(self.keys.kill_log, startat, startat + incr)
    for kill_id in kill_ids:
      kill_data = self.r.hget(self.keys.kill_data, kill_id)
      if kill_data:
        kill = Kill.from_redis(kill_data).resolve_player_ids(self.get_name_from_id)
        kill._id = kill_id
        yield kill

  def get_last_rounds(self, startat=0, incr=20):
    ''' given pagination, get list of most recent Round objects '''
    startat += 1
    round_ids = self.r.zrevrange(self.keys.round_log, startat, startat + incr)
    for round_id in round_ids:
      round_data = self.r.hgetall(self.keys.round_hash(round_id))
      if round_data:
        round_data['round_id'] = round_id
        yield Round(**round_data).resolve_player_ids(self.get_name_from_id)

  def get_top_weapons(self):
    ''' get list of tuples of weapon to kills '''
    results = self.r.zrevrange(self.keys.top_weapons, 0, 20, withscores=True)
    return map(lambda x: (x[0], int(x[1])), results)

  def get_kills_for_date_range(self, startdate=None, previous_days=7):
    ''' get ordered dict of kills per day per given date range '''
    if not isinstance(startdate, datetime):
      startdate = datetime.utcnow()

    stats = OrderedDict()

    for x in range(previous_days):
      current_date = startdate - timedelta(days=x)
      key = self.keys.kills_per_day(str(current_date.date()))
      try:
        count = int(self.r.get(key))
      except (TypeError, ValueError):
        count = 0
      stats[current_date] = count

    return stats

  def get_top_countries(self, limit=10):
    ''' get list of tuples of countries and players from that country '''
    return self.r.zrevrange(self.keys.top_countries, 0, limit, withscores=True)

  def player_search(self, name):
    ''' search for players based on name fragment. return list of Player() objects sorted desc by last seen'''
    # escape glob characters so they act as expected as search terms
    name = name.replace('*', '\*').replace('?', '\?')

    player_ids = set()

    cursor = 0
    tries = 0

    # *maybe* these values are too high under some circumstances?
    max_tries = 100
    max_names = 100

    while tries < max_tries and len(player_ids) < max_names:
        res = self.r.hscan(self.keys.player_search, cursor, '*{name}*'.format(name=name.lower()), max_names)
        cursor = res[0]
        for name in res[1].values():
            player_id = self.get_id_from_name(name)
            if player_id:
                player_ids.add(player_id)
        if cursor == 0:
            break
        tries += 1

    return sorted((self.get_player_fields(player_id, ('lastcountry', 'lastseen', 'firstseen', 'kills')) for player_id in player_ids),
                  key=operator.attrgetter('lastseen'),
                  reverse=True)

  def get_name_from_id(self, player_id):
    ''' get most recent name this id is tied to '''
    names = self.get_all_names_from_id(player_id)
    if names:
      return names[0]
    else:
      return None

  def get_all_names_from_id(self, player_id, limit=10):
    ''' get all names this ID is tied to, sorted by most recent use descending '''
    names = self.r.zrevrange(self.keys.player_id_to_names(player_id), 0, limit)
    return remove_redundant_player_names(names)

  def get_id_from_name(self, name):
    ''' get latest id this name is tied to '''
    return self.r.hget(self.keys.name_to_id, name)

  def hmget_with_keys(self, hash_name, keys):
    ''' like self.r.hgetall except specify the keys you get back '''
    keys = list(keys)

    data = self.r.hmget(hash_name, keys)
    if not data:
      return {}

    return dict(zip(keys, data))
