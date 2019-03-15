from piestats.models.events import EventPlayerJoin, EventNextMap, EventScore, EventInvalidMap, MapList, EventLogChange
from piestats.models.kill import Kill
from piestats.models.round import Round
from piestats.update.hwid import Hwid
from IPy import IP
from datetime import datetime
from itertools import cycle
import pkg_resources
import multiprocessing
from setproctitle import setproctitle
import select
import msgpack
import os

try:
  import GeoIP
except ImportError:
  GeoIP = None


class ApplyKillQueue():
  ''' Use multiple processes to handle incrementing kill stats in redis in parallel '''
  def __init__(self, hwid, r, keys):

    self.hwid = hwid
    self.r = r
    self.keys = keys

    self.pipes = []
    self.procs = []

    self.cycler = None
    self.kill_event = None

  def start_procs(self, nproc):
    ''' Start our worker processes to handle the kills '''
    self.kill_event = multiprocessing.Event()

    my_pid = os.getpid()
    for number in xrange(nproc):
      r_pipe, w_pipe = multiprocessing.Pipe(False)
      proc = multiprocessing.Process(target=self.worker, args=(number, r_pipe, my_pid))
      proc.start()
      self.pipes.append(w_pipe)

    self.cycler = cycle(self.pipes)

  def teardown(self):
    ''' Tear down all worker processes '''
    self.kill_event.set()

    for pipe in self.pipes:
      pipe.close()
    for proc in self.procs:
      proc.join()

    self.pipes = []
    self.procs = []
    self.cycler = None

  def worker(self, number, pipe, original_parent_ppid):
    ''' Listen on its pipe for kill events, and apply them '''
    setproctitle('piestats update worker %d' % number)

    pipe_fd = pipe.fileno()
    try:
      while True:

        rlist, _, _ = select.select([pipe_fd], [], [], .1)

        # Make this process die either when we're told to or if our parent is killed before us
        if self.kill_event.is_set() or os.getppid() != original_parent_ppid:
          pipe.close()
          return

        if pipe_fd in rlist:
          kill_tuple, incr = msgpack.loads(pipe.recv_bytes(), use_list=False)

          kill = Kill.from_tuple(kill_tuple)
          self.apply_kill(kill, incr)

    except KeyboardInterrupt:
      return

  def queue_kill(self, kill, incr):
    ''' Round robin between all kill worker pipes '''
    next(self.cycler).send_bytes(msgpack.dumps((kill.to_tuple(), incr), use_bin_type=False))

  def apply_kill(self, kill, incr=1):
    '''
      Apply a kill, incrementing (or decrementing) all relevant metrics
    '''
    if abs(incr) != 1:
      print 'Invalid increment value for kill: {kill}'.format(kill=kill)
      return

    # Convert victim and killer to their IDs
    kill.victim = self.hwid.get_player_id_from_name(kill.victim)
    kill.killer = self.hwid.get_player_id_from_name(kill.killer)

    pipe = self.r.pipeline()

    # Add kill to our internal log
    if incr == 1:

      kill_id = self.r.incr(self.keys.last_kill_id)
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


class ManageEvents():
  ''' State machine for handling log events and applying them to our datastore '''
  def __init__(self, r, keys, server):
    self.r = r
    self.keys = keys
    self.current_map = None
    self.current_logfile = None
    self.round_id = None
    self.valid_score_maps = set()
    self.ignore_maps = server.ignore_maps
    self.ignore_players = server.ignore_players

    self.hwid = Hwid(self.r, self.keys)

    self.apply_kill_queue = ApplyKillQueue(hwid=self.hwid, keys=keys, r=r)

    self.geoip = None
    if GeoIP:
      try:
        self.geoip = GeoIP.open(pkg_resources.resource_filename('piestats.update', 'GeoIP.dat'), GeoIP.GEOIP_MMAP_CACHE)
      except Exception as e:
        print 'Failed loading geoip file %s' % e
    else:
      print 'GeoIP looking up not supported'

  def __enter__(self):
    ''' When our context manager is initialized, initialize our kill queue '''
    self.apply_kill_queue.start_procs(nproc=multiprocessing.cpu_count())
    return self

  def __exit__(self, type, value, traceback):
    ''' And when it's done, tear them down '''
    self.apply_kill_queue.teardown()

  def apply_event(self, event):
    '''
      Given an event object, determine which method to delegate it
    '''
    if isinstance(event, EventPlayerJoin):
      if event.player not in self.ignore_players:
          player_id = self.hwid.register_hwid(event.player, event.hwid, event.date)
          self.update_country(event.ip, player_id)
          self.update_player_search(event.player)
    elif isinstance(event, EventNextMap):
      self.update_map(event.map, event.date)
    elif isinstance(event, MapList):
      self.update_maps_list(event.maps, event.score_maps)
    elif isinstance(event, EventInvalidMap):
      self.kill_map(event.map)
    elif isinstance(event, EventScore):
      if event.player not in self.ignore_players and (self.current_map is None or self.current_map not in self.ignore_maps):
          self.update_score(self.hwid.get_player_id_from_name(event.player), event.team, event.date)
    elif isinstance(event, Kill):
      if(event.killer not in self.ignore_players and
         event.victim not in self.ignore_players and
         (self.current_map is None or self.current_map not in self.ignore_maps)):
          self.apply_kill(event)
    elif isinstance(event, EventLogChange):
      self.log_change(event.path)

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

  def log_change(self, path):
    ''' Looking at a new logfile. Cleanup/resurrect round. '''

    # Keep track of this so we can refer to it when we create rounds based on map change
    self.current_logfile = path

    # Clean these up as rounds/state don't cross log boundaries
    self.round_id = None
    self.current_map = None

    # It's possible we're still parsing the same logfile as last time, and the
    # last round we saw wasn't finished when we stopped parsing it
    old_round_id = self.r.hget(self.keys.last_round_id_per_log, path)

    if old_round_id:
      old_round_id = int(old_round_id)
      old_round_data = self.r.hgetall(self.keys.round_hash(old_round_id))

      if old_round_data:
        old_round = Round(**old_round_data)

        # If the last round for this logfile is unfinished, continue with it
        if old_round.finished is None:
          print '\nLoaded old unfinished round ID %d from file %s' % (old_round_id, self.current_logfile)
          self.round_id = old_round_id
          self.current_map = old_round.map

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

    # What if the last logged round is empty?
    else:
      old_round_id = self.r.get(self.keys.last_round_id)
      if old_round_id:
        old_round_data = self.r.hgetall(self.keys.round_hash(old_round_id))
        if old_round_data:
          old_round = Round(**old_round_data)

          # If it has no kills or no scores or anything else just delete it
          if old_round.empty:
            print 'Killing old empty round id %s' % old_round_id
            self.r.delete(self.keys.round_hash(old_round_id))
            self.r.zrem(self.keys.round_log, old_round_id)

    self.round_id = None
    self.current_map = map

    if map:

      # Start a new round if this round is using a real map and not a placeholder one
      if map not in self.ignore_maps:
        self.r.zincrby(self.keys.top_maps, map)
        self.round_id = self.r.incr(self.keys.last_round_id)
        self.r.hmset(self.keys.round_hash(self.round_id), {
            'started': date,
            'map': map,
            'flags': 'yes' if self.current_map in self.valid_score_maps else 'no'
        })
        self.r.hset(self.keys.last_round_id_per_log, self.current_logfile, self.round_id)
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
      self.r.hincrby(self.keys.round_hash(self.round_id), 'scores_player:' + team + ':' + str(player))

  def apply_kill(self, kill, incr=1):
    '''
      Apply a kill, incrementing (or decrementing) all relevant metrics
    '''
    if incr == 1:
      if self.current_map:
        kill.map = self.current_map
      if self.round_id:
        kill.round_id = self.round_id

    self.apply_kill_queue.queue_kill(kill, incr)

  def rollback_kill(self, kill, kill_id):
    '''
      Undo a kill, reversing all metrics it increased
    '''

    if kill:
        # Decrement all counters this kill increased
        self.apply_kill(kill, -1)

        # Kill kills per day from this date
        text_today = str(datetime.utcfromtimestamp(kill.date).date())
        self.r.delete(self.keys.kills_per_day(text_today))

    # Kill the kill
    self.r.hdel(self.keys.kill_data, kill_id)
    self.r.zrem(self.keys.kill_log, kill_id)
