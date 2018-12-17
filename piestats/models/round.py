from datetime import datetime
from collections import defaultdict
from piestats.models.player import Player


class Round:
  def __init__(self, *args, **kwargs):
    self.info = kwargs
    self.playerstats = defaultdict(lambda: defaultdict(int))
    self.weaponstats = defaultdict(lambda: defaultdict(int))
    self._winning_player = None

    for key, value in kwargs.iteritems():
      if key.startswith('scores_player:'):
        _, team, player = key.split(':', 2)
        self.playerstats[player]['scores'] = int(value)
        self.playerstats[player][team + '_scores'] = int(value)
      elif key.startswith('kills_player:'):
        _, player = key.split(':', 1)
        self.playerstats[player]['kills'] = int(value)
      elif key.startswith('deaths_player:'):
        _, player = key.split(':', 1)
        self.playerstats[player]['deaths'] = int(value)
      elif key.startswith('kills_weapon:'):
        _, weapon = key.split(':', 1)
        self.weaponstats[weapon]['kills'] = int(value)
        self.weaponstats[weapon]['name'] = weapon

    for player in self.playerstats:
      self.playerstats[player]['name'] = player

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
  def pretty_duration(self):
    duration = self.duration
    if duration:
      hours, remainder = divmod(duration, 3600)
      minutes, seconds = divmod(remainder, 60)
      resp = []

      if hours:
        resp.append('%dh' % hours)

      if minutes:
        resp.append('%dm' % minutes)

      if seconds:
        resp.append('%ds' % seconds)

      return ''.join(resp)
    else:
      return '-'

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
          name=sorted(((player['kills'], player['name']) for player in self.players.itervalues()), reverse=True)[0][1]
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

  def resolve_player_ids(self, resolver):
    '''
      Translate player IDs to names
    '''
    if not self.players:
      return self

    new_players = {}

    for player in self.players.itervalues():
      player['id'] = player['name']
      name = resolver(player['name'])
      player['name'] = name
      new_players[name] = player

    self.players = new_players

    return self
