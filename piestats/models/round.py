from datetime import datetime
from collections import defaultdict
from piestats.models.player import Player
from piestats.models.base import JsonSerializableModel


class Round(JsonSerializableModel):
  ''' Object representing a round '''

  json_fields = ('id', 'started', 'finished', 'duration', 'kills', 'alpha_scores',
                 'bravo_scores', 'map', 'flagmatch', 'tie', 'winning_team',
                 'winning_player', 'players', 'events', 'weapons', 'empty')

  def __init__(self, *args, **kwargs):
    self.info = kwargs
    self.playerstats = defaultdict(lambda: defaultdict(int))
    self.weaponstats = defaultdict(lambda: defaultdict(int))
    self._winning_player = None

    for key, value in kwargs.iteritems():
      if key.startswith('scores_player:'):
        _, team, player_id = key.split(':', 2)
        player_id = int(player_id)
        self.playerstats[player_id]['scores'] = int(value)
        self.playerstats[player_id]['scores:' + team.capitalize()] = int(value)
      elif key.startswith('kills_player:'):
        _, player_id = key.split(':', 1)
        player_id = int(player_id)
        self.playerstats[player_id]['kills'] = int(value)
      elif key.startswith('deaths_player:'):
        _, player_id = key.split(':', 1)
        player_id = int(player_id)
        self.playerstats[player_id]['deaths'] = int(value)
      elif key.startswith('kills_weapon:'):
        _, weapon = key.split(':', 1)
        self.weaponstats[weapon]['kills'] = int(value)
        self.weaponstats[weapon]['name'] = weapon

  def get_int(self, key):
    try:
      return int(self.info.get(key, 0))
    except:
      return 0

  @property
  def id(self):
    return self.get_int('round_id')

  @property
  def started(self):
    ''' Friendly date this round happened '''

    date = self.get_int('started')
    if date:
      return datetime.utcfromtimestamp(date)
    else:
      return None

  @property
  def finished(self):
    ''' Friendly date this round happened '''

    date = self.get_int('finished')
    if date:
      return datetime.utcfromtimestamp(date)
    else:
      return None

  @property
  def duration(self):
    return max(0, self.get_int('finished') - self.get_int('started'))

  @property
  def kills(self):
    ''' Total count of kills '''
    return self.get_int('kills')

  @property
  def scores(self):
    ''' Total count of kills '''
    return self.get_int('scores:Alpha') + self.get_int('scores:Bravo')

  @property
  def alpha_scores(self):
    return self.get_int('scores:Alpha')

  @property
  def bravo_scores(self):
    return self.get_int('scores:Bravo')

  @property
  def map(self):
    ''' Map used during this score '''
    return self.info.get('map')

  @property
  def flagmatch(self):
    return self.info.get('flags') == 'yes'

  @property
  def tie(self):
    return self.scores > 0 and self.alpha_scores == self.bravo_scores

  @property
  def winning_team(self):
    if self.alpha_scores > self.bravo_scores:
      return 'alpha'
    elif self.alpha_scores < self.bravo_scores:
      return 'bravo'

  @property
  def winning_player(self):
    if not self.players:
      return None

    if not self._winning_player:
      self._winning_player = Player(
          name=sorted(((player.kills, player.name) for player in self.players.itervalues()), reverse=True)[0][1]
      )

    return self._winning_player

  @property
  def players(self):
    ''' List of player names with their kills/caps '''
    return self.playerstats

  @property
  def num_players(self):
    ''' List of player names with their kills/caps '''
    return len(self.playerstats)

  @property
  def events(self):
    ''' All events captured during this round. Kills and scores to count '''
    return []

  @property
  def weapons(self):
    return self.weaponstats

  @property
  def empty(self):
    return not self.players and not self.kills and not self.scores

  def resolve_players(self, results):
    '''
      Translate player IDs to names
    '''
    if not self.playerstats:
      return self

    new_players = {}

    for player_id, data in self.playerstats.iteritems():
      player = results.get_player_fields(player_id, ['lastcountry'])
      if not player:
        continue
      player.info.update(data)
      player.info['name'] = results.get_name_from_id(player_id)
      new_players[player.info['name']] = player

    self.playerstats = new_players

    return self
