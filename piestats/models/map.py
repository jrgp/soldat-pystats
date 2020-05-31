from collections import defaultdict
from piestats.models.base import JsonSerializableModel


class Map(JsonSerializableModel):
  ''' Object representing a map '''

  json_fields = ('name', 'flags', 'plays', 'kills', 'scores_alpha', 'scores_bravo',
                 'wins_alpha', 'wins_bravo', 'ties', 'weapons', 'svg_exists', 'title')

  def __init__(self, *args, **kwargs):
    self.info = kwargs
    self.wepstats = defaultdict(lambda: defaultdict(int))
    for key, value in kwargs.items():
      if key.startswith('kills:'):
        stat, wep = key.split(':')
        self.wepstats[wep][stat] = int(value)
        self.wepstats[wep]['name'] = wep

  def get_int(self, key):
    try:
      return int(self.info.get(key, 0))
    except:
      return 0

  @property
  def name(self):
    return self.info.get('name')

  @property
  def title(self):
    return self.info.get('title')

  @property
  def flags(self):
    return self.info.get('flags') == 'yes'

  @property
  def plays(self):
    return self.get_int('plays')

  @property
  def kills(self):
    return self.get_int('kills')

  @property
  def scores_alpha(self):
    return self.get_int('scores:Alpha')

  @property
  def scores_bravo(self):
    return self.get_int('scores:Bravo')

  @property
  def wins_alpha(self):
    return self.get_int('wins:alpha')

  @property
  def wins_bravo(self):
    return self.get_int('wins:bravo')

  @property
  def ties(self):
    return self.get_int('ties')

  @property
  def weapons(self):
    return self.wepstats

  @property
  def svg_exists(self):
    return 'svg_image' in self.info

  @property
  def svg(self):
    return self.info['svg_image']
