import redis
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
from piestats.keys import PystatsKeys

try:
  import cPickle as pickle
except ImportError:
  import pickle


class player:
  def __init__(self, *args, **kwargs):
    self.info = kwargs
    self.wepstats = defaultdict(lambda: defaultdict(int))
    for key, value in kwargs.iteritems():
      if key.startswith('kills:') or key.startswith('deaths:'):
        stat, wep = key.split(':')
        self.wepstats[wep][stat] = int(value)
        self.wepstats[wep]['name'] = wep

  def get(self, key):
    if key not in self.info:
      return None
    return self.info[key]

  @property
  def name(self):
    return self.get('name')

  @property
  def kills(self):
    try:
      return int(self.get('kills'))
    except (KeyError, TypeError):
      return 0

  @property
  def deaths(self):
    try:
      return int(self.get('deaths'))
    except (KeyError, TypeError):
      return 0

  @property
  def firstseen(self):
    timestamp = self.get('firstseen')
    if not timestamp:
      return None
    return datetime.utcfromtimestamp(int(timestamp))

  @property
  def lastseen(self):
    timestamp = self.get('lastseen')
    if not timestamp:
      return None
    return datetime.utcfromtimestamp(int(timestamp))

  @property
  def weapons(self):
    return self.wepstats

  @property
  def lastcountry(self):
    return self.get('lastcountry')


class stats():

  def __init__(self, config):
    self.r = redis.Redis(**config.redis_connect)
    self.keys = PystatsKeys(config)

  def get_top_killers(self, startat=0, incr=20):
    results = self.r.zrevrange(self.keys.top_players, startat, startat + incr, withscores=True)
    for name, kills in results:
      more = {}
      for key in ['deaths', 'lastseen', 'firstseen', 'lastcountry']:
        more[key] = self.r.hget(self.keys.player_hash(name), key)
      yield player(name=name,
                   kills=kills,
                   **more
                   )

  def get_player(self, _player):
    info = self.r.hgetall(self.keys.player_hash(_player))
    if not info:
      return None
    return player(name=_player, **info)

  def get_player_fields(self, _player, fields=[]):
      info = {}
      for key in fields:
        info[key] = self.r.hget(self.keys.player_hash(_player), key)
      return player(name=_player, **info)

  def get_player_top_enemies(self, player):
    pass

  def get_player_top_victims(self, player):
    pass

  def get_last_kills(self, startat=0, incr=20):
    for kill in self.r.lrange(self.keys.kill_log, startat, startat + incr):
      yield pickle.loads(kill)

  def get_top_weapons(self):
    results = self.r.zrevrange(self.keys.top_weapons, 0, 20, withscores=True)
    return map(lambda x: (x[0], int(x[1])), results)

  def get_kills_for_date_range(self, startdate=None, previous_days=7):
    if not isinstance(startdate, datetime):
      startdate = datetime.now()

    stats = OrderedDict()

    for x in range(previous_days):
      current_date = str((startdate - timedelta(days=x)).date())
      key = self.keys.kills_per_day(current_date)
      try:
        count = int(self.r.get(key))
      except (TypeError, ValueError):
        count = 0
      stats[current_date] = count

    return stats

  def get_top_countries(self, limit=10):
    return self.r.zrevrange(self.keys.top_countries, 0, limit, withscores=True)
