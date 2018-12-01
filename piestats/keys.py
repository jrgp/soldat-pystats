class Keys:
  ''' Convenient access to keys we use with redis. Abstracts away different servers. '''

  def __init__(self, config, server):
    self.key_prefix = '%s:%s' % (config.redis_prefix, server.redis_key_prefix)

    # Sorted set for number of kills per player
    self.top_players = '%s:top_players' % self.key_prefix

    # Map of lowercase player name to normal case player name
    self.player_search = '%s:player_search' % self.key_prefix

    # Last numeric kill id, which we increment
    self.last_kill_id = '%s:last_kill_id' % self.key_prefix

    # Sorted set mapping timestamp to kill ID
    self.kill_log = '%s:kill_log' % self.key_prefix

    # Hash mapping kill ID to msgpack kill data
    self.kill_data = '%s:kill_data' % self.key_prefix

    # Sorted set for number of kills per weapon
    self.top_weapons = '%s:top_weapons' % self.key_prefix

    # Sorted set for number of players per country
    self.top_countries = '%s:top_countries' % self.key_prefix

    # Sorted set for number of times each map played
    self.top_maps = '%s:top_maps' % self.key_prefix

    # Last numeric round id, which we increment
    self.last_round_id = '%s:last_round_id' % self.key_prefix

    # Sorted set mapping timestamp to round ID ID
    self.round_log = '%s:round_log' % self.key_prefix

    # Hash containing file size of log paths
    self.log_positions = '%s:log_positions' % self.key_prefix

  def kills_per_day(self, day):
    ''' Plain keys for number of kills that happened on ``day`` '''
    return '%s:kills_per_day:%s' % (self.key_prefix, day)

  def player_hash(self, player):
    ''' Hash of data for player ``player``'''
    return '%s:player:%s' % (self.key_prefix, player)

  def map_hash(self, _map):
    ''' Hash of data for map ``_map``'''
    return '%s:map:%s' % (self.key_prefix, _map)

  def player_top_enemies(self, player):
    ''' Sorted set of people being killed by ``player`` '''
    return '%s:player_top_enemies:%s' % (self.key_prefix, player)

  def player_top_victims(self, player):
    ''' Sorted set of people killing ``player`` '''
    return '%s:player_top_victims:%s' % (self.key_prefix, player)

  def weapon_top_killers(self, weapon):
    ''' Sorted set containing the amount of kills a player using a weapon has '''
    return '%s:weapon_top_killers:%s' % (self.key_prefix, weapon)

  def round_hash(self, round_id):
    ''' Hash of data for round ID ``round_id``'''
    return '%s:round_data:%s' % (self.key_prefix, round_id)
