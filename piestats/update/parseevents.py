import re
import os
import time
from io import BytesIO
from datetime import datetime, date

from piestats.update.pms_parser import PmsReader
from piestats.update.mapimage import generate_map_svg
from piestats.models.events import (EventPlayerJoin, EventNextMap, EventScore, EventInvalidMap, EventRequestMap, EventBareLog,
                                    EventRestart, EventShutdown)
from piestats.models.kill import Kill
from piestats.progressbar import simple_progressbar
from piestats.compat import kill_bytes

flag_round_map_prefixes = ('ctf_', 'inf_', 'tw_')


class ParseEvents():

  def __init__(self, retention, filemanager, r, keys):
    self.r = r
    self.keys = keys
    self.retention = retention
    self.filemanager = filemanager

    kill_regex = (r'(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) \((?P<killer_team>\d)\) (?P<killer>.+) killed \((?P<victim_team>\d)\) (?P<victim>.+) '
                  r'with (?P<weapon>Ak-74|Barrett M82A1|Chainsaw|Cluster Grenades|Combat Knife|Desert Eagles|'
                  r'FN Minimi|Grenade|Hands|HK MP5|LAW|M79|Ruger 77|Selfkill|Spas-12|Stationary gun|Steyr AUG'
                  r'|USSOCOM|XM214 Minigun|Bow|Flame Bow)')

    self.event_regex = (
        (EventPlayerJoin, re.compile(r'(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) (?P<player>.+) joining game \((?P<ip>[^:]+):\d+\) HWID:(?P<hwid>\S+)')),
        (EventNextMap, re.compile(r'(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) Next map: (?P<map>[^$]+)')),
        (EventNextMap, re.compile(r'(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) /map (?P<map>[^(\s]+)')),
        (EventRequestMap, re.compile(r'(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) \[.+\] !map (?P<map>[^(\s]+)')),
        (EventRestart, re.compile(r'(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) /restart \([^\)]+\)$')),
        (EventRestart, re.compile(r'(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) Restarting...$')),
        (EventInvalidMap, re.compile(r'\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d Map not found \((?P<map>\S+)\)')),
        (EventScore, re.compile(r'(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) (?P<player>.+) scores for (?P<team>Alpha|Bravo) Team$')),
        (EventShutdown, re.compile(r'(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) (Signal received, shutting down|Shutting down server)')),
        (Kill, re.compile(kill_regex)),

        # Make absolutely sure this is last
        (EventBareLog, re.compile(r'(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) (?P<line>[^$]+)$')),
    )

  def build_map_names(self):
    map_titles = {}
    flag_score_maps = set()
    score_spawnpoint_types = ('alpha_flag', 'bravo_flag')

    map_paths = self.filemanager.get_file_paths('maps', '*.pms')

    for map_path in simple_progressbar(map_paths,
                                       label='Parsing %d maps' % len(map_paths),
                                       item_show_func=lambda x: 'Parsing ' + os.path.basename(x) if x else None):

      map_filename = os.path.basename(map_path)[:-4]

      do_generate_svg = not self.r.hexists(self.keys.map_hash(map_filename), 'svg_image')

      # If we already have the data for this map in redis, don't bother parsing it again
      map_title = kill_bytes(self.r.hget(self.keys.map_hash(map_filename), 'title'))
      map_flags = kill_bytes(self.r.hget(self.keys.map_hash(map_filename), 'flags'))
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
        print('Failed reading map %s: %s' % (map_path, e))
        continue

      # If we already have the generate svg for this map, don't generate it again
      if do_generate_svg:
          try:
              generated_svg = generate_map_svg(reader)
              self.r.hset(self.keys.map_hash(map_filename), 'svg_image', generated_svg)
          except Exception as e:
              print('Failed generating SVG for %s: %s' % (map_filename, e))

      if not map_title:
          title = kill_bytes(reader.name).strip()
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
          parsed = datetime.strptime(date, '%y-%m-%d %H:%M:%S')
          if self.retention is not None and self.retention.too_old(parsed):
            print('ignoring event {event}'.format(event=event))
            return None

          # Hacks hacks hacks because previous way using time.mktime(parsed.timetuple()) did not have hour precision :|
          data['date'] = int((parsed - datetime(1970, 1, 1)).total_seconds())

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
      yield self.filemanager.filename_key(path), (event for event in self.parse_events(kill_bytes(self.filemanager.get_data(path, position))))

  @classmethod
  def get_time_out_of_filename(cls, filename):
    m = re.match(r'consolelog-(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)-\d+.txt', filename)
    if not m:
      raise ValueError('Cannot parse filename %s' % filename)
    values = m.groupdict()
    seconds = int(time.mktime(date(int(values['year']) + 2000, int(values['month']), int(values['day'])).timetuple()))
    return seconds
