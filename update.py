import redis
import time
import os
import glob
import re
import string
from dateutil import parser
from collections import namedtuple

KillObj = namedtuple('Kill', ['killer', 'victim', 'weapon', 'timestamp', 'suicide'])


class player():
  def __init__(self, name):
    self._name = name
  @property
  def name(self):
    return self._name
  @property
  def data_key(self):
    return 'pystats:playerdata:{name}'.format(name=self.name)
  def __str__(self):
    return self.name


def updateStats(r):
  for kill in getKills(r):
    r.zadd('pystats:playerslastseen', kill.killer.name, kill.timestamp)

    if kill.killer.name != kill.victim.name:
      r.zadd('pystats:playerslastseen', kill.victim.name, kill.timestamp)

    if not kill.suicide:
      r.zincrby('pystats:playerstopkills', kill.killer.name)

    r.zincrby('pystats:playerstopdeaths', kill.killer.name)

    if not kill.suicide:
      r.hincrby(kill.killer.data_key, 'kills', 1)
    r.hincrby(kill.victim.data_key, 'deaths', 1)

    r.hsetnx(kill.killer.data_key, 'firstseen', kill.timestamp)
    r.hset(kill.killer.data_key, 'lastseen', kill.timestamp)

    r.hsetnx(kill.victim.data_key, 'firstseen', kill.timestamp) 
    r.hset(kill.victim.data_key, 'lastseen', kill.timestamp)

    if kill.suicide:
      r.zincrby('pystats:weaponsuicides', kill.weapon)
    else:
      r.zincrby('pystats:weaponkills', kill.weapon)
      r.hincrby(kill.killer.data_key, 'kills:' + kill.weapon, 1)
      r.hincrby(kill.victim.data_key, 'deaths:' + kill.weapon, 1)


def parseKills(contents):
    m = re.findall('\-\-\- (\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d)\\n(.+)\\n(.+)\\n(Ak-74|Barrett M82A1|'
    'Chainsaw|Cluster Grenades|Combat Knife|Desert Eagles|FN Minimi|Grenade|Hands|HK MP5|LAW|M79|Ruger '
    '77|Selfkill|Spas-12|Stationary gun|Steyr AUG|USSOCOM|XM214 Minigun)\n', contents)
    for kill in m:
      timestamp, killer, victim, weapon = map(string.strip, kill)
      suicide = killer == victim

      unixtime = int(time.mktime(parser.parse(timestamp, parser.parserinfo(yearfirst=True)).timetuple()))
      yield KillObj(
        player(killer),
        player(victim),
        weapon,
        unixtime,
        suicide
      )


def getKills(r):
  root = '/root/pyredis_stats/kills'
  for path in glob.glob(os.path.join(root, '*.txt')):
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
        contents = h.read()
        for kill in parseKills(contents):
          yield kill
      r.set(key, size)
    else:
      print 'skipping unchanged {filename}'.format(filename=filename)



def main():
  r = redis.Redis()
  updateStats(r)

if __name__ == '__main__':
  main()
