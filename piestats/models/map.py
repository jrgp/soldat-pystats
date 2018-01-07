from collections import defaultdict


class Map:
  def __init__(self, *args, **kwargs):
    self.info = kwargs
    self.wepstats = defaultdict(lambda: defaultdict(int))
    for key, value in kwargs.iteritems():
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
  def weapons(self):
    return self.wepstats
