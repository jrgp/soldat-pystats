import re
import os
import time
from io import BytesIO
from dateutil import parser

from piestats.update.pms_parser import PmsReader
from piestats.models.events import EventPlayerJoin, EventNextMap, EventScore, EventInvalidMap, EventRequestMap, EventBareLog, MapList
from piestats.models.kill import Kill

flag_round_map_prefixes = ('ctf_', 'inf_', 'tw_')


class ParseEvents():

  def __init__(self, retention, filemanager, r, keys):
    self.r = r
    self.keys = keys
    self.retention = retention
    self.filemanager = filemanager
    self.parse_kill_date_parserinfo = parser.parserinfo(yearfirst=True)

    kill_regex = ('(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) \((?P<killer_team>\d)\) (?P<killer>.+) killed \((?P<victim_team>\d)\) (?P<victim>.+) '
                  'with (?P<weapon>Ak-74|Barrett M82A1|Chainsaw|Cluster Grenades|Combat Knife|Desert Eagles|'
                  'FN Minimi|Grenade|Hands|HK MP5|LAW|M79|Ruger 77|Selfkill|Spas-12|Stationary gun|Steyr AUG'
                  '|USSOCOM|XM214 Minigun|Bow|Flame Bow)')

    self.event_regex = (
        (EventPlayerJoin, re.compile('\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d (?P<player>.+) joining game \((?P<ip>[^:]+):\d+\) HWID:\S+')),
        (EventNextMap, re.compile('(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) Next map: (?P<map>[^$]+)')),
        (EventNextMap, re.compile('(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) /map (?P<map>[^(\s]+)')),
        (EventRequestMap, re.compile('(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) \[.+\] !map (?P<map>[^(\s]+)')),
        (EventInvalidMap, re.compile('\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d Map not found \((?P<map>\S+)\)')),
        (EventScore, re.compile('(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) (?P<player>.+) scores for (?P<team>Alpha|Bravo) Team$')),
        (self.generate_kill, re.compile(kill_regex)),

        # Make absolutely sure this is last
        (EventBareLog, re.compile('(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) (?P<line>[^$]+)$')),
    )

    self.requested_map = None
    self.requested_map_change = None
    self.map_titles = {}

  def build_map_names(self):
    map_titles = {}
    flag_score_maps = set()
    score_spawnpoint_types = ('alpha_flag', 'bravo_flag')

    map_paths = self.filemanager.get_file_paths('maps', '*.pms')

    print 'Parsing %d maps' % len(map_paths)

    for map_path in map_paths:

      map_filename = os.path.basename(map_path)[:-4]

      # If we already have the data for this map in redis, don't bother parsing it again
      map_title = self.r.hget(self.keys.map_hash(map_filename), 'title')
      map_flags = self.r.hget(self.keys.map_hash(map_filename), 'flags')
      if map_title:
        map_titles[map_filename] = map_title
        if map_flags == 'yes':
          flag_score_maps.add(map_filename)
        continue

      content = self.filemanager.get_data(map_path, 0)

      reader = PmsReader()

      try:
        reader.parse(BytesIO(content))
      except Exception as e:
        print 'Failed reading map %s: %s' % (map_path, e)
        continue

      title = reader.header.Name.text[:reader.header.Name.length].strip()
      map_titles[map_filename] = title

      self.r.hset(self.keys.map_hash(map_filename), 'title', title)

      if any(map_filename.lower().startswith(prefix) for prefix in flag_round_map_prefixes):
        for spawnpoint in reader.spawnpoints:
          if spawnpoint.TypeText in score_spawnpoint_types:
            flag_score_maps.add(map_filename)
            self.r.hset(self.keys.map_hash(map_filename), 'flags', 'yes')
            break

    return map_titles, flag_score_maps

  def parse_line(self, line):
    for event, regex in self.event_regex:
      m = regex.match(line.strip())
      if not m:
        continue

      data = m.groupdict()

      # Add datetimes manually for non kills
      if event != self.generate_kill:
        date = data.get('date')
        if date:
          parsed = parser.parse(date, self.parse_kill_date_parserinfo)
          if parsed:
            # Ignore ancient events
            if self.retention.too_old(parsed):
              return None
            data['date'] = int(time.mktime(parsed.timetuple()))

      return event(**data)

  def parse_events(self, contents):
    for line in contents.splitlines():
      event = self.parse_line(line)
      if event is None:
          continue

      # If it's a next map event, swallow it and do some logic
      if isinstance(event, EventNextMap) or isinstance(event, EventRequestMap):
        if event.map in self.map_titles:
          self.requested_map = event.map
        else:
          self.requested_map = None
        yield EventNextMap(map=None, date=event.date)
        continue

      # If it's a bare log event, see if it's the start message for that new map we almost got.
      # If it is, yield the change map event
      if isinstance(event, EventBareLog) and self.requested_map is not None:
          if event.line.strip() == self.map_titles[self.requested_map]:
              yield EventNextMap(map=self.requested_map, date=event.date)
              self.requested_map = None
              continue

      # Otherwise just yield the event
      yield event

  def get_events(self):
    '''
      Get all events from relevant console log files
    '''

    with self.filemanager.initialize():
      self.map_titles, flag_score_maps = self.build_map_names()

      # Provide list of valid maps
      if self.map_titles and flag_score_maps:
          yield MapList(maps=self.map_titles, score_maps=flag_score_maps)

      for path, position in self.filemanager.get_files('logs', 'consolelog*.txt'):
        for event in self.parse_events(self.filemanager.get_data(path, position)):
          yield event

  def generate_kill(self, *args, **kwargs):
    date = parser.parse(kwargs['date'], self.parse_kill_date_parserinfo)

    if self.retention.too_old(date):
      return None

    if kwargs['weapon'] == 'Flame Bow':
      kwargs['weapon'] = 'Bow'

    return Kill(
        kwargs['killer'],
        kwargs['victim'],
        kwargs['weapon'],
        int(time.mktime(date.timetuple())),
        kwargs['killer_team'],
        kwargs['victim_team'])
