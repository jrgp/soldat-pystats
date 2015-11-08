import redis
from datetime import datetime
from collections import defaultdict
from piestats.player import PlayerObj  # noqa

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

  player_hash_key = 'pystats:playerdata:{player}'

  def __init__(self):
    self.r = redis.Redis()

  def get_top_killers(self, startat=0, incr=20):
    results = self.r.zrevrange('pystats:playerstopkills', startat, startat + incr, withscores=True)
    for name, kills in results:
      more = {}
      for key in ['deaths', 'lastseen', 'firstseen', 'lastcountry']:
        more[key] = self.r.hget(self.player_hash_key.format(player=name), key)
      yield player(name=name,
                   kills=kills,
                   **more
                   )

  def get_player(self, _player):
    info = self.r.hgetall(self.player_hash_key.format(player=_player))
    if not info:
      return None
    return player(name=_player, **info)

  def get_player_fields(self, _player, fields=[]):
      info = {}
      for key in fields:
        info[key] = self.r.hget(self.player_hash_key.format(player=_player), key)
      return player(name=_player, **info)

  def get_last_kills(self, startat=0, incr=20):
    for kill in self.r.lrange('pystats:latestkills', startat, startat + incr):
      yield pickle.loads(kill)

  def get_top_weapons(self):
    results = self.r.zrevrange('pystats:weaponkills', 0, 20, withscores=True)
    return results
