from collections import namedtuple
from geoip import geolite2
from IPy import IP
import re
import os
import glob
import click

EventPlayerJoin = namedtuple('EventPlayerJoin', ['player', 'ip'])
EventNextMap = namedtuple('EventNextMap', ['map'])


def progress_function(item):
  if item:
    return 'Parsing {0}'.format(item)


def get_events(r, keys, soldat_dir):
  root = os.path.join(soldat_dir, 'logs')

  # Make sure we go by filename sorted in ascending order, as we can't sort
  # our global kill log after items are inserted.
  files = sorted(map(os.path.basename, glob.glob(os.path.join(root, 'consolelog*.txt'))))

  with click.progressbar(files,
                         label='Parsing {0} console logs'.format(len(files)),
                         show_eta=False,
                         item_show_func=progress_function) as progressbar:
    for filename in progressbar:
      path = os.path.join(root, filename)
      key = keys.log_file(filename=path)
      size = os.path.getsize(path)
      prev = r.get(key)
      if prev is None:
        pos = 0
      else:
        pos = int(prev)
      if size > prev:
        if progressbar.is_hidden:
          print('Reading {filename} from offset {pos}'.format(filename=filename, pos=pos))
        with open(path, 'r') as h:
          h.seek(pos)
          for event in parse_events(h):
            yield event
        r.set(key, size)


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
  if not r.exists(keys.player_hash(player)):
    return
  if IP(ip).iptype() != 'PUBLIC':
    return
  match = geolite2.lookup(ip)
  if not match:
    return
  country_code = match.country
  if r.hset(keys.player_hash(player), 'lastcountry', country_code):
    r.zincrby(keys.top_countries, country_code)


def update_map(r, keys, map):
  r.zincrby(keys.top_maps, map)
