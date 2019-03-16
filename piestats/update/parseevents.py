import re
import os
import time
from io import BytesIO
from datetime import datetime

from piestats.update.pms_parser import PmsReader
from piestats.update.mapimage import generate_map_svg
from piestats.models.events import (EventPlayerJoin, EventNextMap, EventScore, EventInvalidMap, EventRequestMap, EventBareLog,
                                    EventRestart, EventShutdown)
from piestats.models.kill import Kill

flag_round_map_prefixes = ('ctf_', 'inf_', 'tw_')


class ParseEvents():

  def __init__(self, retention, filemanager, r, keys):
    self.r = r
    self.keys = keys
    self.retention = retention
    self.filemanager = filemanager

    kill_regex = ('(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) \((?P<killer_team>\d)\) (?P<killer>.+) killed \((?P<victim_team>\d)\) (?P<victim>.+) '
                  'with (?P<weapon>Ak-74|Barrett M82A1|Chainsaw|Cluster Grenades|Combat Knife|Desert Eagles|'
                  'FN Minimi|Grenade|Hands|HK MP5|LAW|M79|Ruger 77|Selfkill|Spas-12|Stationary gun|Steyr AUG'
                  '|USSOCOM|XM214 Minigun|Bow|Flame Bow)')

    self.event_regex = (
        (EventPlayerJoin, re.compile('(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) (?P<player>.+) joining game \((?P<ip>[^:]+):\d+\) HWID:(?P<hwid>\S+)')),
        (EventNextMap, re.compile('(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) Next map: (?P<map>[^$]+)')),
        (EventNextMap, re.compile('(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) /map (?P<map>[^(\s]+)')),
        (EventRequestMap, re.compile('(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) \[.+\] !map (?P<map>[^(\s]+)')),
        (EventRestart, re.compile('(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) /restart \([^\)]+\)$')),
        (EventRestart, re.compile('(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) Restarting...$')),
        (EventInvalidMap, re.compile('\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d Map not found \((?P<map>\S+)\)')),
        (EventScore, re.compile('(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) (?P<player>.+) scores for (?P<team>Alpha|Bravo) Team$')),
        (EventShutdown, re.compile('(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) (Signal received, shutting down|Shutting down server)')),
        (Kill, re.compile(kill_regex)),

        # Make absolutely sure this is last
        (EventBareLog, re.compile('(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) (?P<line>[^$]+)$')),
    )

  def build_map_names(self):
    map_titles = {}
    flag_score_maps = set()
    score_spawnpoint_types = ('alpha_flag', 'bravo_flag')

    map_paths = self.filemanager.get_file_paths('maps', '*.pms')

    print 'Parsing %d maps' % len(map_paths)

    for map_path in map_paths:

      map_filename = os.path.basename(map_path)[:-4]

      do_generate_svg = not self.r.hexists(self.keys.map_hash(map_filename), 'svg_image')

      # If we already have the data for this map in redis, don't bother parsing it again
      map_title = self.r.hget(self.keys.map_hash(map_filename), 'title')
      map_flags = self.r.hget(self.keys.map_hash(map_filename), 'flags')
      if map_title:
        map_titles[map_filename] = map_title
        if map_flags == 'yes':
          flag_score_maps.add(map_filename)
        if not do_generate_svg:
            continue

      content = self.filemanager.get_data(map_path, 0)

      reader = PmsReader()

      try:
        reader.parse(BytesIO(content))
      except Exception as e:
        print 'Failed reading map %s: %s' % (map_path, e)
        continue

      # If we already have the generate svg for this map, don't generate it again
      if do_generate_svg:
          try:
              generated_svg = generate_map_svg(reader)
              self.r.hset(self.keys.map_hash(map_filename), 'svg_image', generated_svg)
              print 'Saved generated SVG for %s' % map_filename
          except Exception as e:
              print 'Failed generating SVG for %s: %s' % (map_filename, e)

      if not map_title:
          title = reader.header.Name.text[:reader.header.Name.length].strip()
          map_titles[map_filename] = title

          self.r.hset(self.keys.map_hash(map_filename), 'title', title)

          if map_filename.lower().startswith(flag_round_map_prefixes):
            for spawnpoint in reader.spawnpoints:
              if spawnpoint.TypeText in score_spawnpoint_types:
                flag_score_maps.add(map_filename)
                self.r.hset(self.keys.map_hash(map_filename), 'flags', 'yes')
                break

    return map_titles, flag_score_maps

  def parse_line(self, line):
    '''
      Run our regexes against a line and return the first event object that matches
    '''
    for event, regex in self.event_regex:
      m = regex.match(line)
      if not m:
        continue

      data = m.groupdict()

      # Parse dates and ignore ancient events
      date = data.get('date')
      if date:
          parsed = datetime.strptime(data['date'], '%y-%m-%d %H:%M:%S')
          if self.retention.too_old(parsed):
            return None
          data['date'] = int(time.mktime(parsed.timetuple()))

      return event(**data)

  def parse_events(self, contents):
    '''
      Run through a text file and yield all events we find in it
    '''
    for line in contents.splitlines():
      event = self.parse_line(line.strip())
      if event:
        yield event

  def get_events(self):
    '''
      Get all events from relevant console log files
    '''

    for path, position in self.filemanager.get_files('logs', 'consolelog*.txt'):
      yield self.filemanager.filename_key(path), (event for event in self.parse_events(self.filemanager.get_data(path, position)))
