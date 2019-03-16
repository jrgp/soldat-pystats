from piestats.models.round import Round


class RoundManager():
  def __init__(self, r, keys, flag_score_maps):
    self.r = r
    self.keys = keys
    self.flag_score_maps = flag_score_maps

  def tweak_last_round(self):
    ''' If the last round for this server is empty, delete it'''
    round_id = self.r.get(self.keys.last_round_id)
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

    data = self.r.hgetall(self.keys.round_hash(int(round_id)))
    if data:
      return Round(**data)

  def get_old_round_for_log(self, logfile):
    ''' Get last round from this log file if there is one and if it is unfinished '''

    round_id = self.r.hget(self.keys.last_round_id_per_log, logfile)
    if round_id:
      old_round = self.get_round_by_id(round_id)
      if old_round.finished is None:
        return old_round

  def new_round(self, map, date, logfile):
    ''' Start new round off and store its map and start date '''

    if not map:
      raise ValueError('Will not make a new round with no map')

    if not date:
      raise ValueError('Will not make a new round with no date')

    self.r.zincrby(self.keys.top_maps, map)
    round_id = int(self.r.incr(self.keys.last_round_id))
    self.r.hmset(self.keys.round_hash(round_id), {
        'started': date,
        'map': map,
        'flags': 'yes' if map in self.flag_score_maps else 'no'
    })
    self.r.hset(self.keys.last_round_id_per_log, logfile, round_id)
    self.r.zadd(self.keys.round_log, round_id, date)

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
      self.r.hset(self.keys.round_hash(round_id), 'finished', date)
      if old_round.winning_team:
        self.r.hincrby(self.keys.map_hash(old_round.map), 'wins:' + old_round.winning_team)
      elif old_round.tie:
        self.r.hincrby(self.keys.map_hash(old_round.map), 'ties')
