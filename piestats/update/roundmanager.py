from piestats.models.round import Round
from piestats.update.parseevents import ParseEvents
from piestats.compat import strip_bytes_from_dict, kill_bytes


class RoundManager():
  def __init__(self, r, keys, flag_score_maps):
    self.r = r
    self.keys = keys
    self.flag_score_maps = flag_score_maps

  def tweak_last_round(self):
    ''' If the last round for this server is empty, delete it'''
    round_id = kill_bytes(self.r.get(self.keys.last_round_id))
    if round_id is not None:
      round_id = int(round_id)
      last_round = self.get_round_by_id(round_id)
      if last_round:
        if last_round.empty:
          self.delete_round(round_id)

  def delete_round(self, round_id):
    ''' Delete a round '''
    self.r.delete(self.keys.round_hash(round_id))
    self.r.zrem(self.keys.round_log, round_id)

  def get_round_by_id(self, round_id):
    ''' Given a round ID, get back a round object with all info on it, or None '''

    round_id = int(round_id)

    data = strip_bytes_from_dict(self.r.hgetall(self.keys.round_hash(round_id)))
    data['round_id'] = round_id
    if data:
      return Round(**data)

  def get_old_round_for_log(self, logfile):
    ''' Get last round from this log file if there is one and if it is unfinished '''

    round_id = strip_bytes_from_dict(self.r.hget(self.keys.last_round_id_per_log, logfile))
    if round_id:
      old_round = self.get_round_by_id(round_id)
      if old_round.started and old_round.finished is None:
        return old_round

  def new_round(self, current_map, date, logfile):
    ''' Start new round off and store its map and start date '''

    if not current_map:
      raise ValueError('Will not make a new round with no map')

    if not date:
      raise ValueError('Will not make a new round with no date')

    self.r.zincrby(self.keys.top_maps, value=current_map, amount=1)
    round_id = int(self.r.incr(self.keys.last_round_id))
    self.r.hmset(self.keys.round_hash(round_id), {
        'started': date,
        'map': current_map,
        'flags': 'yes' if current_map in self.flag_score_maps else 'no',
        'original_logfile': logfile  # for debugging purposes
    })
    self.r.hset(self.keys.last_round_id_per_log, logfile, round_id)
    self.r.zadd(self.keys.round_log, {round_id: date})
    self.r.set(self.keys.last_logfile, logfile)

    return round_id

  def finalize_round(self, round_id, date):
    ''' Finalize round and delete it if its empty '''

    old_round = self.get_round_by_id(round_id)
    if not old_round:
      raise ValueError('Round %d not found' % round_id)

    if not date:
      raise ValueError('Will not end round %d with no date' % round_id)

    if old_round.empty:
      self.delete_round(round_id)
    else:
      started = int(old_round.info['started'])
      if started > date:
        # This mostly happens if a previous update was interrupted
        print('Not finalizing round %d with a date (%d) older than the start date (%d)' % (round_id, date, started))
        return
      self.r.hset(self.keys.round_hash(round_id), 'finished', date)
      if old_round.winning_team:
        self.r.hincrby(self.keys.map_hash(old_round.map), 'wins:' + old_round.winning_team)
      elif old_round.tie:
        self.r.hincrby(self.keys.map_hash(old_round.map), 'ties')

      # Ensure all players have a team set. If they don't, look back at previous
      # rounds
      if old_round.flagmatch:
        need_teams = set()
        for player, data in old_round.playerstats.items():
          if 'team' not in data:
            need_teams.add(player)
        for x in range(5):
          if not need_teams:
            break
          prev_round_id = round_id - x
          prev_round = self.get_round_by_id(prev_round_id)
          if prev_round:
            for player in list(need_teams):
              if player in prev_round.playerstats and 'team' in prev_round.playerstats[player]:
                self.r.hset(self.keys.round_hash(round_id), 'team_player:%s' % player, prev_round.playerstats[player]['team'])
                need_teams.discard(player)

  def get_last_round_from_last_file(self, logfile):
    ''' Get the last round we worked on if it occurred before this filename '''
    last_logfile = kill_bytes(self.r.get(self.keys.last_logfile))
    if last_logfile is not None and self.logfile_comparable(logfile, last_logfile) and self.logfile_greater(logfile, last_logfile):
      round_id = kill_bytes(self.r.hget(self.keys.last_round_id_per_log, last_logfile))
      if round_id:
        old_round = self.get_round_by_id(round_id)
        if old_round.started:
          return old_round
    return None

  @classmethod
  def logfile_comparable(cls, logfile1, logfile2):
    ''' See if two logfile paths are part of the same server '''
    # see if paths are the same exact for last bit. not using os.path as
    # the leading logsource prefix would break it
    dir1 = '/'.join(logfile1.split('/')[:-1])
    dir2 = '/'.join(logfile2.split('/')[:-1])
    return dir1 == dir2

  @classmethod
  def logfile_greater(cls, logfile1, logfile2):
    ''' See if one logfile path (logfile1) came after another comparable logfile path (logfile2) '''
    if not cls.logfile_comparable(logfile1, logfile2):
      raise ValueError('Logfiles %s and %s are not comparable' % (logfile1, logfile2))

    filename1 = logfile1.split('/')[-1]
    filename2 = logfile2.split('/')[-1]

    time1 = ParseEvents.get_time_out_of_filename(filename1)
    time2 = ParseEvents.get_time_out_of_filename(filename2)

    # f the date in the files is the same, compare the last bit after the date in consolelog-19-03-16-04.txt
    if time2 == time1:
      trailer1 = int(filename1.split('-')[-1].split('.')[0])
      trailer2 = int(filename2.split('-')[-1].split('.')[0])
      return trailer1 > trailer2
    else:
      return time1 > time2
