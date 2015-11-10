from collections import namedtuple
from geoip import geolite2
import re
import os
import glob

EventPlayerJoin = namedtuple('EventPlayerJoin', ['player', 'ip'])
EventNextMap = namedtuple('EventNextMap', ['map'])


def get_events(r, keys, soldat_dir):
  skipped_files = 0
  root = os.path.join(soldat_dir, 'logs')

  # Make sure we go by filename sorted in ascending order, as we can't sort
  # our global kill log after items are inserted.
  files = sorted(map(os.path.basename, glob.glob(os.path.join(root, 'consolelog*.txt'))))

  skipped_files = 0

  for filename in files:
    key = keys.log_file(filename=filename)
    path = os.path.join(root, filename)
    size = os.path.getsize(path)
    prev = r.get(key)
    if prev is None:
      pos = 0
    else:
      pos = int(prev)
    if size > prev:
      print 'reading {filename} from offset {pos}'.format(filename=filename, pos=pos)
      with open(path, 'r') as h:
        h.seek(pos)
        for event in parse_events(h):
          yield event
      r.set(key, size)
    else:
      skipped_files += 1

  print 'skipped {count} unchanged console logs'.format(count=skipped_files)


def parse_events(contents):
  header = '\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d '
  event_regexen = [
      (EventPlayerJoin, re.compile(''.join([header, '(?P<player>.+) joining game \((?P<ip>[^:]+):\d+\) HWID:\S+']))),
      (EventNextMap, re.compile(''.join([header, 'Next map: (?P<map>[^$]+)']))),
  ]

  for line in contents:
    for event, regex in event_regexen:
      m = regex.match(line)
      if not m:
        continue
      yield event(**m.groupdict())


def update_events(r, keys, soldat_dir):
  for event in get_events(r, keys, soldat_dir):
    if isinstance(event, EventPlayerJoin):
      update_country(r, keys, event.ip, event.player)
    elif isinstance(event, EventNextMap):
      update_map(r, keys, event.map)


def update_country(r, keys, ip, player):
  match = geolite2.lookup(ip)
  if not match:
    return
  country_code = match.country
  if r.hset(keys.player_hash(player), 'lastcountry', country_code):
    r.zincrby(keys.top_countries, country_code)


def update_map(r, keys, map):
  r.zincrby(keys.top_maps, map)
