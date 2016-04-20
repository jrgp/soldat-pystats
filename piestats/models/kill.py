from datetime import datetime


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
