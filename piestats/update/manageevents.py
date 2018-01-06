from piestats.models.events import EventPlayerJoin, EventNextMap, EventScore, EventInvalidMap, MapList
from piestats.models.kill import Kill
from IPy import IP
from datetime import datetime
import pkg_resources

try:
  import GeoIP
except ImportError:
  GeoIP = None


class ManageEvents():
  def __init__(self, r, keys):
    self.r = r
    self.keys = keys
    self.current_map = None
    self.valid_score_maps = set()

    self.geoip = None
    if GeoIP:
      try:
        self.geoip = GeoIP.open(pkg_resources.resource_filename('piestats.update', 'GeoIP.dat'), GeoIP.GEOIP_MMAP_CACHE)
      except Exception as e:
        print 'Failed loading geoip file %s' % e
    else:
      print 'GeoIP looking up not supported'

  def apply_event(self, event):
    '''
      Given an event object, determine which method to delegate it
    '''
    if isinstance(event, EventPlayerJoin):
      self.update_country(event.ip, event.player)
      self.update_player_search(event.player)
    elif isinstance(event, EventNextMap):
      self.update_map(event.map, event.date)
    elif isinstance(event, MapList):
      self.update_maps_list(event.maps, event.score_maps)
    elif isinstance(event, EventInvalidMap):
      self.kill_map(event.map)
    elif isinstance(event, EventScore):
      self.update_score(event.player, event.team, event.date)
    elif isinstance(event, Kill):
      self.apply_kill(event)

  def update_player_search(self, player):
      '''
        Update the search hash. keys are player lowercase to player normal case. Search
        works by wild card matching contents of the hash to get full player names
      '''
      self.r.hset(self.keys.player_search, player.lower(), player)

  def update_country(self, ip, player):
    '''
      Set player\'s country based on IP they joined with
    '''
    if not self.geoip:
      return
    if IP(ip).iptype() != 'PUBLIC':
      return
    country_code = self.geoip.country_code_by_addr(ip)
    if not country_code:
      return
    if self.r.hset(self.keys.player_hash(player), 'lastcountry', country_code):
      self.r.zincrby(self.keys.top_countries, country_code)

  def update_maps_list(self, maps, score_maps):
      self.valid_score_maps = score_maps

  def update_map(self, map, date):
    '''
      Increase number of times this map has been played
    '''
    self.current_map = map
    if map:
      self.r.zincrby(self.keys.top_maps, map)

  def kill_map(self, map):
    '''
      This event happens to nullify a previous self.current_map in case it was an invalid map
    '''
    if self.current_map == map:
      self.r.zrem(self.keys.top_maps, map)
      self.current_map = None

  def update_score(self, player, team, date):
    '''
      Increase number of times this player has scored, including which team
    '''

    if not self.current_map or self.current_map not in self.valid_score_maps:
      return

    self.r.hincrby(self.keys.player_hash(player), 'scores')
    self.r.hincrby(self.keys.player_hash(player), 'scores:' + team)

    # Map stats
    self.r.hincrby(self.keys.map_hash(self.current_map), 'scores')
    self.r.hincrby(self.keys.map_hash(self.current_map), 'scores:' + team)

    # Player stats
    self.r.hincrby(self.keys.player_hash(player), 'scores_map:' + self.current_map + ':' + team)

  def apply_kill(self, kill, incr=1):
    '''
      Apply a kill, incrementing (or decrementing) all relevant metrics
    '''
    if abs(incr) != 1:
      print 'Invalid increment value for kill: {kill}'.format(kill=kill)
      return

    # Add kill to our internal log
    if incr == 1:
      self.r.lpush(self.keys.kill_log, kill.to_redis())

    # Map logic
    if self.current_map:
      if kill.suicide:
        self.r.hincrby(self.keys.map_hash(self.current_map), 'suicides', incr)
        self.r.hincrby(self.keys.map_hash(self.current_map), 'suicides:' + kill.weapon, incr)
        self.r.hincrby(self.keys.player_hash(kill.victim), 'suicides_map:' + self.current_map, incr)
      else:
        self.r.hincrby(self.keys.map_hash(self.current_map), 'kills', incr)
        self.r.hincrby(self.keys.map_hash(self.current_map), 'kills:' + kill.weapon, incr)

        # Player kills per this map
        self.r.hincrby(self.keys.player_hash(kill.killer), 'kills_map:' + self.current_map, incr)
        self.r.hincrby(self.keys.player_hash(kill.victim), 'deaths_map:' + self.current_map, incr)

    # Stuff that only makes sense for non suicides
    if not kill.suicide:
      self.r.zincrby(self.keys.top_players, kill.killer, incr)
      self.r.hincrby(self.keys.player_hash(kill.killer), 'kills', incr)

    # Increment number of deaths for victim
    self.r.hincrby(self.keys.player_hash(kill.victim), 'deaths', incr)

    # Update first/last time we saw player
    if incr == 1:
      self.r.hsetnx(self.keys.player_hash(kill.killer), 'firstseen', kill.timestamp)

      # Don't overwrite a previous bigger value with a smaller value
      old_last_seen = int(self.r.hget(self.keys.player_hash(kill.killer), 'lastseen') or 0)

      if kill.timestamp > old_last_seen:
        self.r.hset(self.keys.player_hash(kill.killer), 'lastseen', kill.timestamp)

    # Update first/last time we saw victim, if they're not the same..
    if incr == 1 and not kill.suicide:
      self.r.hsetnx(self.keys.player_hash(kill.victim), 'firstseen', kill.timestamp)

      # Don't overwrite a previous bigger value with a smaller value
      old_last_seen = int(self.r.hget(self.keys.player_hash(kill.victim), 'lastseen') or 0)

      if kill.timestamp > old_last_seen:
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
