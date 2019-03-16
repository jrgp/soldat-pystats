from piestats.models.kill import Kill
from piestats.models.events import EventPlayerJoin, EventScore
from datetime import datetime
from IPy import IP


class ApplyEvents:
  ''' Update counters/stats within redis with regards to generated events '''
  def __init__(self, hwid, keys, r, geoip):
    self.hwid = hwid
    self.keys = keys
    self.geoip = geoip
    self.r = r

  def apply(self, decorated_event):
    ''' Given an event, apply it to redis '''
    event = decorated_event.event
    t = type(event)

    if isinstance(event, Kill):
      self.apply_kill(event)

    elif t == EventPlayerJoin:
      player_id = self.hwid.register_hwid(event.player, event.hwid, event.date)
      self.update_country(event.ip, player_id)
      self.update_player_search(event.player)

    elif t == EventScore:
      self.update_score(self.hwid.get_player_id_from_name(event.player), event.team, event.date, decorated_event.map, decorated_event.round_id)

  def update_country(self, ip, player_id):
    ''' Set player's country based on IP they joined with '''
    if not self.geoip:
      return
    if IP(ip).iptype() != 'PUBLIC':
      return
    country_code = self.geoip.country_code_by_addr(ip)
    if not country_code:
      return
    if self.r.hset(self.keys.player_hash(player_id), 'lastcountry', country_code):
      self.r.zincrby(self.keys.top_countries, country_code)

  def update_player_search(self, player_name):
    ''' Keep track of our player search database '''
    self.r.hset(self.keys.player_search, player_name.lower(), player_name)

  def update_score(self, player, team, date, map, round_id):
    ''' Update scores for this team/round/map/player '''

    self.r.hincrby(self.keys.player_hash(player), 'scores')
    self.r.hincrby(self.keys.player_hash(player), 'scores:' + team)

    # Map stats
    self.r.hincrby(self.keys.map_hash(map), 'scores')
    self.r.hincrby(self.keys.map_hash(map), 'scores:' + team)

    # Player stats
    self.r.hincrby(self.keys.player_hash(player), 'scores_map:' + map + ':' + team)

    # Round stats
    if round_id:
      self.r.hincrby(self.keys.round_hash(round_id), 'scores:' + team)
      self.r.hincrby(self.keys.round_hash(round_id), 'scores_player:' + team + ':' + str(player))

  def apply_kill(self, kill, incr=1):
    '''
      Apply a kill, incrementing (or decrementing) all relevant metrics
    '''
    if abs(incr) != 1:
      print 'Invalid increment value for kill: {kill}'.format(kill=kill)
      return

    # Convert victim and killer to their IDs
    kill.victim = int(self.hwid.get_player_id_from_name(kill.victim))
    kill.killer = int(self.hwid.get_player_id_from_name(kill.killer))

    pipe = self.r.pipeline()

    # Add kill to our internal log
    if incr == 1:

      kill_id = int(self.r.incr(self.keys.last_kill_id))
      pipe.hset(self.keys.kill_data, kill_id, kill.to_redis())
      pipe.zadd(self.keys.kill_log, kill_id, kill.date)

    # Map logic
    if kill.map:
      if kill.suicide:
        pipe.hincrby(self.keys.map_hash(kill.map), 'suicides', incr)
        pipe.hincrby(self.keys.map_hash(kill.map), 'suicides:%s' % kill.weapon, incr)
        pipe.hincrby(self.keys.player_hash(kill.victim), 'suicides_map:%s' % kill.map, incr)
      else:
        pipe.hincrby(self.keys.map_hash(kill.map), 'kills', incr)
        pipe.hincrby(self.keys.map_hash(kill.map), 'kills:%s' % kill.weapon, incr)

        # Player kills per this map
        pipe.hincrby(self.keys.player_hash(kill.killer), 'kills_map:%s' % kill.map, incr)
        pipe.hincrby(self.keys.player_hash(kill.victim), 'deaths_map:%s' % kill.map, incr)

    # Stuff that only makes sense for non suicides
    if not kill.suicide:
      pipe.zincrby(self.keys.top_players, kill.killer, incr)
      pipe.hincrby(self.keys.player_hash(kill.killer), 'kills', incr)

      if incr == 1 and kill.round_id:
        pipe.hincrby(self.keys.round_hash(kill.round_id), 'kills_player:%s' % kill.killer)
        pipe.hincrby(self.keys.round_hash(kill.round_id), 'kills')
        pipe.hincrby(self.keys.round_hash(kill.round_id), 'deaths_player:%s' % kill.victim)

    # Increment number of deaths for victim
    pipe.hincrby(self.keys.player_hash(kill.victim), 'deaths', incr)

    # Update first/last time we saw player
    if incr == 1:
      pipe.hsetnx(self.keys.player_hash(kill.killer), 'firstseen', kill.date)

      # Don't overwrite a previous bigger value with a smaller value
      old_last_seen = int(self.r.hget(self.keys.player_hash(kill.killer), 'lastseen') or 0)

      if kill.date > old_last_seen:
        pipe.hset(self.keys.player_hash(kill.killer), 'lastseen', kill.date)

    # Update first/last time we saw victim, if they're not the same..
    if incr == 1 and not kill.suicide:
      pipe.hsetnx(self.keys.player_hash(kill.victim), 'firstseen', kill.date)

      # Don't overwrite a previous bigger value with a smaller value
      old_last_seen = int(self.r.hget(self.keys.player_hash(kill.victim), 'lastseen') or 0)

      if kill.date > old_last_seen:
        pipe.hset(self.keys.player_hash(kill.victim), 'lastseen', kill.date)

    # Update weapon stats..
    if not kill.suicide:
      pipe.zincrby(self.keys.top_weapons, kill.weapon)
      pipe.hincrby(self.keys.player_hash(kill.killer), 'kills:%s' % kill.weapon, incr)
      pipe.hincrby(self.keys.player_hash(kill.victim), 'deaths:%s' % kill.weapon, incr)

      if incr == 1 and kill.round_id:
        pipe.hincrby(self.keys.round_hash(kill.round_id), 'kills_weapon:%s' % kill.weapon)

    # If we're not a suicide, update top enemy kills for playepipe..
    if not kill.suicide:
      # Top people the killer has killed
      pipe.zincrby(self.keys.player_top_enemies(kill.killer), kill.victim, incr)

      # Top people the victim has died by
      pipe.zincrby(self.keys.player_top_victims(kill.victim), kill.killer, incr)

    # If we're not a sucide, add this legit kill to the number of kills for this
    # day
    if incr == 1 and not kill.suicide:
      text_today = str(datetime.utcfromtimestamp(kill.date).date())
      pipe.incr(self.keys.kills_per_day(text_today), incr)

    pipe.execute()

  def rollback_kill(self, kill, kill_id):
    ''' Kill a kill '''
    if kill:
      # Decrement all counters this kill increased
      self.apply_kill(kill, -1)

      # Kill kills per day from this date
      text_today = str(datetime.utcfromtimestamp(kill.date).date())
      self.r.delete(self.keys.kills_per_day(text_today))

    # Kill the kill
    self.r.hdel(self.keys.kill_data, kill_id)
    self.r.zrem(self.keys.kill_log, kill_id)
