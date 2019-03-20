from datetime import datetime
from collections import defaultdict
from piestats.models.base import JsonSerializableModel


class Player(JsonSerializableModel):
  ''' Object representing a player '''

  # Whitelist of object properties to be given when serialized to json
  json_fields = ('name', 'kills', 'deaths', 'firstseen', 'lastseen', 'weapons', 'kd',
                 'lastcountry', 'scores_alpha', 'scores_bravo', 'maps', 'names')

  def __init__(self, *args, **kwargs):
    self.info = kwargs
    self.wepstats = defaultdict(lambda: defaultdict(int))
    self.mapstats = defaultdict(lambda: defaultdict(int))
    for key, value in kwargs.iteritems():

      try:
        value = int(value)
      except:
        value = 0

      key_parts = key.split(':')

      # Parse kills/deaths out of map
      if key.startswith('kills:') or key.startswith('deaths:'):
        stat, wep = key_parts
        self.wepstats[wep][stat] = value
        self.wepstats[wep]['name'] = wep

      # Map stats
      elif key.startswith('scores_map:'):
        _, map_name, team = key_parts
        self.mapstats[map_name]['scores_' + team.lower()] = value

      elif key.startswith('kills_map:'):
        map_name = key_parts[1]
        self.mapstats[map_name]['kills'] = value

      elif key.startswith('deaths_map:'):
        map_name = key_parts[1]
        self.mapstats[map_name]['deaths'] = value

      elif key.startswith('suicides_map:'):
        map_name = key_parts[1]
        self.mapstats[map_name]['suicides'] = value

  def get_int(self, key):
    try:
      return int(self.info.get(key, 0))
    except:
      return 0

  @property
  def name(self):
    return self.info.get('name')

  @property
  def kills(self):
    return self.get_int('kills')

  @property
  def deaths(self):
    return self.get_int('deaths')

  @property
  def firstseen(self):
    timestamp = self.info.get('firstseen')
    if not timestamp:
      return None
    return datetime.utcfromtimestamp(int(timestamp))

  @property
  def lastseen(self):
    timestamp = self.info.get('lastseen')
    if not timestamp:
      return None
    return datetime.utcfromtimestamp(int(timestamp))

  @property
  def weapons(self):
    return self.wepstats

  @property
  def lastcountry(self):
    return self.info.get('lastcountry')

  @property
  def scores_alpha(self):
    return self.get_int('scores:Alpha')

  @property
  def scores_bravo(self):
    return self.get_int('scores:Bravo')

  @property
  def maps(self):
    for key in self.mapstats:
      self.mapstats[key]['name'] = key
    return self.mapstats

  @property
  def names(self):
    return self.info.get('names', [])

  @property
  def kd(self):
    if self.deaths < 1:
      return self.kills

    if self.kills < 1:
      return 0

    return round(float(self.kills) / self.deaths, 2)
