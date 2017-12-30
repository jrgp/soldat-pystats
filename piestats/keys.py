class Keys:
  ''' Convenient access to keys we use with redis. Abstracts away different servers. '''

  def __init__(self, config, server):
    self.key_prefix = '%s:%s' % (config.redis_prefix, server.redis_key_prefix)

    # Sorted set for number of kills per player
    self.top_players = '%s:top_players' % self.key_prefix

    # Map of lowercase player name to normal case player name
    self.player_search = '%s:player_search' % self.key_prefix

    # list containing pickled Kill instances
    self.kill_log = '%s:kill_log' % self.key_prefix

    # Sorted set for number of kills per weapon
    self.top_weapons = '%s:top_weapons' % self.key_prefix

    # Sorted set for number of players per country
    self.top_countries = '%s:top_countries' % self.key_prefix

    # Sorted set for number of times each map played
    self.top_maps = '%s:top_maps' % self.key_prefix

  def kills_per_day(self, day):
    ''' Plain keys for number of kills that happened on ``day`` '''
    return '%s:kills_per_day:%s' % (self.key_prefix, day)

  def player_hash(self, player):
    ''' Hash of data for player ``player``'''
    return '%s:player:%s' % (self.key_prefix, player)

  def log_file(self, filename):
    ''' Plain keys containing file size of ``filename`` '''
    return '%s:logs:%s' % (self.key_prefix, filename)

  def player_top_enemies(self, player):
    ''' Sorted set of people being killed by ``player`` '''
    return '%s:player_top_enemies:%s' % (self.key_prefix, player)

  def player_top_victims(self, player):
    ''' Sorted set of people killing ``player`` '''
    return '%s:player_top_victims:%s' % (self.key_prefix, player)

  def weapon_top_killers(self, weapon):
    ''' Sorted set containing the amount of kills a player using a weapon has '''
    return '%s:weapon_top_killers:%s' % (self.key_prefix, weapon)
