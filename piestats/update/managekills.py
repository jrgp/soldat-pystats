try:
  import cPickle as pickle
except ImportError:
  import pickle
from datetime import datetime


class ManageKills():
  def __init__(self, r, keys):
    self.r = r
    self.keys = keys

  def apply_kill(self, kill, incr=1):

    if abs(incr) != 1:
      print 'Invalid increment value for kill: {kill}'.format(kill=kill)
      return

    # Add kill to our internal log
    if incr == 1:
      self.r.lpush(self.keys.kill_log, pickle.dumps(kill))

    # Stuff that only makes sense for non suicides
    if not kill.suicide:
      self.r.zincrby(self.keys.top_players, kill.killer, incr)
      self.r.hincrby(self.keys.player_hash(kill.killer), 'kills', incr)

    # Increment number of deaths for victim
    self.r.hincrby(self.keys.player_hash(kill.victim), 'deaths', incr)

    # Update first/last time we saw player
    if incr == 1:
      self.r.hsetnx(self.keys.player_hash(kill.killer), 'firstseen', kill.timestamp)
      self.r.hset(self.keys.player_hash(kill.killer), 'lastseen', kill.timestamp)

    # Update first/last time we saw victim, if they're not the same..
    if incr == 1 and not kill.suicide:
      self.r.hsetnx(self.keys.player_hash(kill.victim), 'firstseen', kill.timestamp)
      self.r.hset(self.keys.player_hash(kill.victim), 'lastseen', kill.timestamp)

    # Update weapon stats..
    if not kill.suicide:
      self.r.zincrby(self.keys.top_weapons, kill.weapon)
      self.r.hincrby(self.keys.player_hash(kill.killer), 'kills:' + kill.weapon, incr)
      self.r.hincrby(self.keys.player_hash(kill.victim), 'deaths:' + kill.weapon, incr)

    # If we're not a suicide, update top enemy kills for playeself.r..
    if not kill.suicide:
      # Top people the killer has killed
      self.r.zincrby(self.keys.player_top_enemies(kill.killer), kill.victim, incr)

      # Top people the victim has died by
      self.r.zincrby(self.keys.player_top_victims(kill.victim), kill.killer, incr)

    # If we're not a sucide, add this legit kill to the number of kills for this
    # day
    if not kill.suicide:
      text_today = str(datetime.utcfromtimestamp(kill.timestamp).date())
      self.r.incr(self.keys.kills_per_day(text_today), incr)

  def rollback_kill(self, kill):

    # Decrement all counters this kill increased
    self.apply_kill(kill, -1)

    text_today = str(datetime.utcfromtimestamp(kill.timestamp).date())
    self.r.delete(self.keys.kills_per_day(text_today))
    self.r.rpop(self.keys.kill_log)
