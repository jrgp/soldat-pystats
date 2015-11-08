from collections import namedtuple
from geoip import geolite2
import re
import os
import glob
from piestats.player import PlayerObj

EventPlayerJoin = namedtuple('EventPlayerJoin', ['player', 'ip'])
EventNextMap = namedtuple('EventNextMap', ['map'])


def get_events(r, soldat_dir):
  root = os.path.join(soldat_dir, 'logs')
  for path in glob.glob(os.path.join(root, 'consolelog-*.txt')):
    filename = os.path.basename(path)
    key = 'pystats:logs:{filename}'.format(filename=filename)
    size = os.path.getsize(path)
    prev = r.get(key)
    if prev is None:
      pos = 0
    else:
      pos = prev
    if size > prev:
      print 'reading {filename} from offset {pos}'.format(filename=filename, pos=pos)
      with open(path, 'r') as h:
        h.seek(pos)
        for event in parse_events(h):
          yield event
      r.set(key, size)
    else:
      print 'skipping unchanged {filename}'.format(filename=filename)


def parse_events(contents):
  header = '\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d '
  event_regexen = [
      (EventPlayerJoin, re.compile(''.join(header, '(?P<player>+) joining game \((?P<ip>[^:]+):\d+\) HWID:\S+'))),
      (EventNextMap, re.compile(''.join(header, 'Next map: (?P<map>[^$]+)'))),
  ]

  for line in contents:
    for event, regex in event_regexen:
      m = regex.match(line)
      if not line:
        continue
      yield event(**m.groupdict())


def update_events(r, soldat_dir):
  for event in get_events(r, soldat_dir):
    if isinstance(event, EventPlayerJoin):
      update_country(r, event.ip, PlayerObj(event.player))
    elif isinstance(event, EventNextMap):
      update_maps(r, event.map)


def update_country(r, ip, player):
  match = geolite2.lookup(ip)
  if not match:
    return
  country_code = match.country
  if r.hset(player.data_key, 'lastcountry', country_code):
    r.zincrby('pystats:topcountries', country_code)


def update_maps(r, map):
  r.zincrby('pystats:topmaps', map)
