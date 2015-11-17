class Keys:
  ''' Convenient access to keys we use with redis. Abstracts away different servers. '''

  def __init__(self, config, server):
    self.redis_prefix = config.redis_prefix
    self.server_prefix = server.redis_key_prefix

  @property
  def top_players(self):
    ''' Sorted set for number of kills per player '''
    return ':'.join((self.redis_prefix, self.server_prefix, 'top_players'))

  @property
  def kill_log(self):
    ''' list containing pickled Kill instances '''
    return ':'.join((self.redis_prefix, self.server_prefix, 'kill_log'))

  @property
  def top_weapons(self):
    ''' Sorted set for number of kills per weapon '''
    return ':'.join((self.redis_prefix, self.server_prefix, 'top_weapons'))

  @property
  def top_countries(self):
    ''' Sorted set for number of players per country '''
    return ':'.join((self.redis_prefix, self.server_prefix, 'top_countries'))

  @property
  def top_maps(self):
    ''' Sorted set for number of times each map played '''
    return ':'.join((self.redis_prefix, self.server_prefix, 'top_maps'))

  @property
  def top_map_kills(self):
    ''' Sorted set for number of times people have killed in each map '''
    return ':'.join((self.redis_prefix, self.server_prefix, 'top_map_kills'))

  def kills_per_day(self, day):
    ''' Plain keys for number of kills that happened on ``day`` '''
    return ':'.join((self.redis_prefix, self.server_prefix, 'kills_per_day', day))

  def player_hash(self, player):
    ''' Hash of data for player ``player``'''
    return ':'.join((self.redis_prefix, self.server_prefix, 'player', player))

  def log_file(self, filename):
    ''' Plain keys containing file size of ``filename`` '''
    return ':'.join((self.redis_prefix, self.server_prefix, 'logs', filename))

  def player_top_enemies(self, player):
    ''' Sorted set of people being killed by ``player`` '''
    return ':'.join((self.redis_prefix, self.server_prefix, 'player_top_enemies', player))

  def player_top_victims(self, player):
    ''' Sorted set of people killing ``player`` '''
    return ':'.join((self.redis_prefix, self.server_prefix, 'player_top_victims', player))

  def weapon_top_killers(self, weapon):
    ''' Sorted set containing the amount of kills a player using a weapon has '''
    return ':'.join((self.redis_prefix, self.server_prefix, 'weapon_top_killers', weapon))
