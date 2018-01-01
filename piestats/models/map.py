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

  def get(self, key):
    if key not in self.info:
      return None
    return self.info[key]

  @property
  def name(self):
    return self.get('name')

  @property
  def plays(self):
    try:
      return int(self.get('plays'))
    except TypeError:
      return 0

  @property
  def kills(self):
    try:
      return int(self.get('kills'))
    except TypeError:
      return 0

  @property
  def scores_alpha(self):
    try:
      return int(self.get('scores:Alpha'))
    except TypeError:
      return 0

  @property
  def scores_bravo(self):
    try:
      return int(self.get('scores:Bravo'))
    except TypeError:
      return 0

  @property
  def weapons(self):
    return self.wepstats
