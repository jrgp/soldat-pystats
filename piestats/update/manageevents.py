from piestats.models.events import EventPlayerJoin, EventNextMap, EventScore
from piestats.models.kill import Kill
from geoip import geolite2
from IPy import IP
try:
  import cPickle as pickle
except ImportError:
  import pickle
from datetime import datetime


class ManageEvents():
  def __init__(self, r, keys):
    self.r = r
    self.keys = keys

  def apply_event(self, event):
    '''
      Given an event object, determine which method to delegate it
    '''
    if isinstance(event, EventPlayerJoin):
      self.update_country(event.ip, event.player)
    elif isinstance(event, EventNextMap):
      self.update_map(event.map)
    elif isinstance(event, EventScore):
      self.update_score(event.player, event.team)
    elif isinstance(event, Kill):
      self.apply_kill(event)

  def update_country(self, ip, player):
    '''
      Set player\'s country based on IP they joined with
    '''
    if IP(ip).iptype() != 'PUBLIC':
      return
    match = geolite2.lookup(ip)
    if not match:
      return
    country_code = match.country
    if self.r.hset(self.keys.player_hash(player), 'lastcountry', country_code):
      self.r.zincrby(self.keys.top_countries, country_code)

  def update_map(self, map):
    '''
      Increase number of times this map has been played
    '''
    self.r.zincrby(self.keys.top_maps, map)

  def update_score(self, player, team):
    '''
      Increase number of times this player has scored, including which team
    '''
    self.r.hincrby(self.keys.player_hash(player), 'scores')
    self.r.hincrby(self.keys.player_hash(player), 'scores:' + team)

  def apply_kill(self, kill, incr=1):
    '''
      Apply a kill, incrementing (or decrementing) all relevant metrics
    '''
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
    '''
      Undo a kill, reversing all metrics it increased
    '''

    # Decrement all counters this kill increased
    self.apply_kill(kill, -1)

    text_today = str(datetime.utcfromtimestamp(kill.timestamp).date())
    self.r.delete(self.keys.kills_per_day(text_today))
    self.r.rpop(self.keys.kill_log)
