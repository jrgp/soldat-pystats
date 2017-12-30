from datetime import datetime
import msgpack


class Kill():
  def __init__(self, killer, victim, weapon, timestamp):
    self.killer = killer
    self.victim = victim
    self.weapon = weapon
    self.timestamp = timestamp

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

  @classmethod
  def from_redis(cls, item):
    '''
      Class factory to instantiate a new instance of this class based on a msgpack
      representation
    '''
    return cls(*msgpack.loads(item))

  def to_redis(self):
    '''
      Dump the kill to msgpack. Just a tuple with the args used to create this class
    '''
    return msgpack.dumps((self.killer, self.victim, self.weapon, self.timestamp))
