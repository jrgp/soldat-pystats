import redis
from datetime import datetime, timedelta
from collections import OrderedDict
from piestats.keys import Keys
from piestats.models.player import Player
from piestats.models.map import Map
from piestats.models.kill import Kill


class Results():
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
    try:
      return int(self.r.zcard(self.keys.top_players))
    except ValueError:
      return 0

  def get_num_maps(self):
    try:
      return int(self.r.zcard(self.keys.top_maps))
    except ValueError:
      return 0

  def get_top_killers(self, startat=0, incr=20):
    results = self.r.zrevrange(self.keys.top_players, startat, startat + incr, withscores=True)
    for name, kills in results:
      more = {}
      for key in ['deaths', 'lastseen', 'firstseen', 'lastcountry', 'scores:Alpha', 'scores:Bravo']:
        more[key] = self.r.hget(self.keys.player_hash(name), key)
      yield Player(name=name,
                   kills=kills,
                   **more
                   )

  def get_top_maps(self, startat=0, incr=20):
    results = self.r.zrevrange(self.keys.top_maps, startat, startat + incr, withscores=True)
    for name, plays in results:
      more = {}
      for key in ['scores:Alpha', 'scores:Bravo', 'kills']:
        more[key] = self.r.hget(self.keys.map_hash(name), key)
      yield Map(name=name,
                plays=plays,
                **more
                )

  def get_player(self, _player):
    info = self.r.hgetall(self.keys.player_hash(_player))
    if not info:
      return None
    return Player(name=_player, **info)

  def get_player_fields(self, _player, fields=[]):
    info = {}
    for key in fields:
      info[key] = self.r.hget(self.keys.player_hash(_player), key)
    return Player(name=_player, **info)

  def get_player_top_enemies(self, _player, startat=0, incr=20):
    results = self.r.zrevrange(self.keys.player_top_enemies(_player), 0, startat + incr, withscores=True)
    for name, their_kills in results:
      more = {}
      for key in ['lastcountry']:
        more[key] = self.r.hget(self.keys.player_hash(name), key)
      my_deaths = float(self.r.zscore(self.keys.player_top_enemies(name), _player) or 0)
      more['kd'] = '%.2f' % (their_kills / my_deaths if my_deaths > 0 else 0)
      yield Player(name=name,
                   kills=their_kills,
                   **more
                   )

  def get_player_top_victims(self, _player, startat=0, incr=20):
    results = self.r.zrevrange(self.keys.player_top_victims(_player), 0, startat + incr, withscores=True)
    for name, my_kills in results:
      more = {}
      for key in ['lastcountry']:
        more[key] = self.r.hget(self.keys.player_hash(name), key)
      their_deaths = float(self.r.zscore(self.keys.player_top_victims(name), _player) or 0)
      more['kd'] = '%.2f' % (my_kills / their_deaths if their_deaths > 0 else 0)
      yield Player(name=name,
                   kills=my_kills,
                   **more
                   )

  def get_last_kills(self, startat=0, incr=20):
    kill_ids = self.r.zrevrange(self.keys.kill_log, startat, startat + incr)
    for kill_id in kill_ids:
      kill_data = self.r.hget(self.keys.kill_data, kill_id)
      if kill_data:
        yield Kill.from_redis(kill_data)

  def get_top_weapons(self):
    results = self.r.zrevrange(self.keys.top_weapons, 0, 20, withscores=True)
    return map(lambda x: (x[0], int(x[1])), results)

  def get_kills_for_date_range(self, startdate=None, previous_days=7):
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
    return self.r.zrevrange(self.keys.top_countries, 0, limit, withscores=True)

  def get_weapon_stats(self, name):
    kills = self.r.zscore(self.keys.top_weapons, name)
    if kills is None:
      return False

  def player_search(self, name):
    # escape glob characters so they act as expected as search terms
    name = name.replace('*', '\*').replace('?', '\?')

    names = set()

    cursor = 0
    tries = 0

    # *maybe* these values are too high under some circumstances?
    max_tries = 100
    max_names = 100

    while tries < max_tries and len(names) < max_names:
        res = self.r.hscan(self.keys.player_search, cursor, '*{name}*'.format(name=name.lower()), max_names)
        cursor = res[0]
        if cursor == 0:
            break
        names.update(res[1].values())
        tries += 1

    # pair each name with the number of kills this player has, and sort it by player name.
    players_with_kills = sorted((name, self.r.zscore(self.keys.top_players, name)) for name in names)

    return [player for player in players_with_kills if player[1] > 0]
