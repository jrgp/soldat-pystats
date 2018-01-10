from piestats.models.events import EventPlayerJoin, EventNextMap, EventScore, EventInvalidMap, MapList
from piestats.models.kill import Kill
from piestats.models.round import Round
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
    self.round_id = None
    self.valid_score_maps = set()
    self.lobby_maps = ('Lothic', 'Lobby')

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
      Increase number of times this map has been played, and start keeping track of round
      events
    '''

    # Kill current round
    if self.round_id:
      self.r.hset(self.keys.round_hash(self.round_id), 'finished', date)
      old_round_id = self.round_id
      old_map = self.current_map

      # Finish up old round's stats
      if old_map:
        old_round_data = self.r.hgetall(self.keys.round_hash(old_round_id))
        if old_round_data:
          old_round = Round(**old_round_data)

          # If it has no kills or no scores or anything else just delete it
          if old_round.empty:
            self.r.delete(self.keys.round_hash(old_round_id))
            self.r.zrem(self.keys.round_log, old_round_id)
          else:

            # Otherwise update wins/ties for map stats
            if old_round.winning_team:
              self.r.hincrby(self.keys.map_hash(old_map), 'wins:' + old_round.winning_team)
            elif old_round.tie:
              self.r.hincrby(self.keys.map_hash(old_map), 'ties')

    self.round_id = None
    self.current_map = map

    if map:
      self.r.zincrby(self.keys.top_maps, map)

      # Start a new round if this round is using a real map and not a placeholder one
      if map not in self.lobby_maps:
        self.round_id = self.r.incr(self.keys.last_round_id)
        self.r.hmset(self.keys.round_hash(self.round_id), {
            'started': date,
            'map': map,
            'flags': 'yes' if self.current_map in self.valid_score_maps else 'no'
        })
        self.r.zadd(self.keys.round_log, self.round_id, date)

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

    # Round stats
    if self.round_id:
      self.r.hincrby(self.keys.round_hash(self.round_id), 'scores:' + team)
      self.r.hincrby(self.keys.round_hash(self.round_id), 'scores_player:' + team + ':' + player)

  def apply_kill(self, kill, incr=1):
    '''
      Apply a kill, incrementing (or decrementing) all relevant metrics
    '''
    if abs(incr) != 1:
      print 'Invalid increment value for kill: {kill}'.format(kill=kill)
      return

    # Add kill to our internal log
    if incr == 1:

      # Tie it to this round
      if self.round_id:
        kill.round_id = self.round_id

      kill_id = self.r.incr(self.keys.last_kill_id)
      self.r.hset(self.keys.kill_data, kill_id, kill.to_redis())
      self.r.zadd(self.keys.kill_log, kill_id, kill.timestamp)

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

      if incr == 1 and self.round_id:
        self.r.hincrby(self.keys.round_hash(self.round_id), 'kills_player:' + kill.killer)
        self.r.hincrby(self.keys.round_hash(self.round_id), 'kills')
        self.r.hincrby(self.keys.round_hash(self.round_id), 'deaths_player:' + kill.victim)

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

      if incr == 1 and self.round_id:
        self.r.hincrby(self.keys.round_hash(self.round_id), 'kills_weapon:' + kill.weapon)

    # If we're not a suicide, update top enemy kills for playeself.r..
    if not kill.suicide:
      # Top people the killer has killed
      self.r.zincrby(self.keys.player_top_enemies(kill.killer), kill.victim, incr)

      # Top people the victim has died by
      self.r.zincrby(self.keys.player_top_victims(kill.victim), kill.killer, incr)

    # If we're not a sucide, add this legit kill to the number of kills for this
    # day
    if incr == 1 and not kill.suicide:
      text_today = str(datetime.utcfromtimestamp(kill.timestamp).date())
      self.r.incr(self.keys.kills_per_day(text_today), incr)

  def rollback_kill(self, kill, kill_id):
    '''
      Undo a kill, reversing all metrics it increased
    '''

    if kill:
        # Decrement all counters this kill increased
        self.apply_kill(kill, -1)

        # Kill kills per day from this date
        text_today = str(datetime.utcfromtimestamp(kill.timestamp).date())
        self.r.delete(self.keys.kills_per_day(text_today))

    # Kill the kill
    self.r.hdel(self.keys.kill_data, kill_id)
    self.r.zrem(self.keys.kill_log, kill_id)
