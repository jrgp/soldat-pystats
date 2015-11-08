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
    self.wepstats = defaultdict(dict)
    for key, value in kwargs.iteritems():
      if key.startswith('kills:') or key.startswith('deaths:'):
        stat, wep = key.split(':')
        self.wepstats[wep][stat] = value

  def get(self, key):
    if key not in self.info:
      return None
    return self.info[key]

  @property
  def name(self):
    return self.get('name')

  @property
  def kills(self):
    return self.get('kills')

  @property
  def deaths(self):
    return self.get('deaths')

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


class stats():

  player_hash_key = 'pystats:playerdata:{player}'

  def __init__(self):
    self.r = redis.Redis()

  def get_top_killers(self, top=20):
    results = self.r.zrevrange('pystats:playerstopkills', 0, top, withscores=True)
    for name, kills in results:
      yield player(name=name, kills=int(kills))

  def get_player(self, _player):
    info = self.r.hgetall(self.player_hash_key.format(player=_player))
    if not info:
      return None
    return player(name=_player, **info)

  def get_last_kills(self, startat=0, incr=20):
    for kill in self.r.lrange('pystats:latestkills', startat, startat + incr):
      data = pickle.loads(kill)
      yield data
