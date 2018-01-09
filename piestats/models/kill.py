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
  def __init__(self, killer, victim, weapon, timestamp, killer_team=-1, victim_team=-1):
    self.killer = killer
    self.victim = victim
    self.weapon = weapon
    self.timestamp = timestamp
    self._killer_team = int(killer_team)
    self._victim_team = int(victim_team)

  @property
  def suicide(self):
    '''
      Kill is suicide if killer is victim or weapon is Selfkill
    '''
    return self.killer == self.victim or self.weapon == 'Selfkill'

  @property
  def datetime(self):
    '''
      Get timestamp in python datetime format instead of int
    '''
    return datetime.utcfromtimestamp(int(self.timestamp))

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
    return msgpack.dumps((self.killer, self.victim, self.weapon, self.timestamp, self._killer_team, self._victim_team), use_bin_type=False)
