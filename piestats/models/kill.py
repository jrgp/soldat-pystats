from datetime import datetime
import msgpack

team_names = (
    'none',
    'alpha',
    'bravo',
    'charlie',
    'delta',
    'spectator'
)


class Kill():
  def __init__(self, killer, victim, weapon, date, killer_team=-1, victim_team=-1, round_id=0, map=None):
    if weapon == 'Flame Bow':
        weapon = 'Bow'
    self.killer = killer
    self.victim = victim
    self.weapon = weapon
    self.date = date
    self._killer_team = int(killer_team)
    self._victim_team = int(victim_team)
    self.round_id = round_id
    self.map = map

  @property
  def suicide(self):
    '''
      Kill is suicide if killer is victim or weapon is Selfkill
    '''
    return self.killer == self.victim or self.weapon == 'Selfkill'

  @property
  def datetime(self):
    '''
      Get date in python datetime format instead of int
    '''
    return datetime.utcfromtimestamp(int(self.date))

  @property
  def killer_team(self):
    if self._killer_team == -1:
      return None
    return team_names[self._killer_team]

  @property
  def victim_team(self):
    if self._victim_team == -1:
      return None
    return team_names[self._victim_team]

  @classmethod
  def from_redis(cls, item):
    '''
      Class factory to instantiate a new instance of this class based on a msgpack
      representation
    '''
    return cls(*msgpack.loads(item, use_list=False))

  def to_redis(self):
    '''
      Dump the kill to msgpack. Just a tuple with the args used to create this class
    '''
    return msgpack.dumps(self.to_tuple(), use_bin_type=False)

  def to_tuple(self):
    return (self.killer, self.victim, self.weapon, self.date, self._killer_team, self._victim_team, self.round_id, self.map)

  @classmethod
  def from_tuple(cls, item):
    return cls(*item)

  def resolve_player_ids(self, resolver):
    '''
      Translate player IDs to names
    '''
    self.killer = resolver(self.killer)
    self.victim = resolver(self.victim)
    return self
