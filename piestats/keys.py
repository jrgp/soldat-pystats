class PystatsKeys():
  '''Convenient access to keys we use with redis'''

  def __init__(self, config):
    self.prefix = config.redis_prefix

  @property
  def top_players(self):
    ''' Sorted set for number of kills per player '''
    return ':'.join((self.prefix, 'top_players'))

  @property
  def kill_log(self):
    ''' list containing pickled KillObj instances '''
    return ':'.join((self.prefix, 'kill_log'))

  @property
  def top_weapons(self):
    ''' Sorted set for number of kills per weapon '''
    return ':'.join((self.prefix, 'top_weapons'))

  @property
  def top_countries(self):
    ''' Sorted set for number of players per country '''
    return ':'.join((self.prefix, 'top_countries'))

  @property
  def top_maps(self):
    ''' Sorted set for number of times each map played '''
    return ':'.join((self.prefix, 'top_maps'))

  @property
  def players_last_seen(self):
    ''' Sorted set with item being player name and score being unix time stamp  '''
    return ':'.join((self.prefix, 'players_last_seen'))

  def kills_per_day(self, day):
    ''' Plain keys for number of kills that happened on ``day`` '''
    return ':'.join((self.prefix, 'kills_per_day', day))

  def player_hash(self, player):
    ''' Hash of data for player ``player``'''
    return ':'.join((self.prefix, 'player', player))

  def log_file(self, filename):
    ''' Plain keys containing file size of ``filename`` '''
    return ':'.join((self.prefix, 'logs', filename))

  def player_top_enemies(self, player):
    ''' Sorted set of people being killed by ``player`` '''
    return ':'.join((self.prefix, 'player_top_enemies', player))

  def player_top_victims(self, player):
    ''' Sorted set of people killing ``player`` '''
    return ':'.join((self.prefix, 'player_top_victims', player))
