from datetime import datetime
from collections import defaultdict


class Player:
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
