import os
import glob
import re
import string
from dateutil import parser
from datetime import datetime
import time

try:
  import cPickle as pickle
except ImportError:
  import pickle

from piestats.models.kill import Kill


def get_kills(r, keys, retention, soldat_dir):
  root = os.path.join(soldat_dir, 'logs', 'kills')

  # Make sure we go by filename sorted in ascending order, as we can't sort
  # our global kill log after items are inserted.
  files = sorted(map(os.path.basename, glob.glob(os.path.join(root, '*.txt'))))

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
    if size > pos:
      print('reading {filename} from offset {pos}'.format(filename=filename, pos=pos))
      with open(path, 'r') as h:
        h.seek(pos)
        for kill in parse_kills(h.read(), retention):
          yield kill
      r.set(key, size)
    else:
      skipped_files += 1

  print('skipped {count} unchanged kill logs'.format(count=skipped_files))


def parse_kills(contents, retention):
    m = re.findall('\-\-\- (\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d)\\n(.+)\\n(.+)\\n(Ak-74|Barrett M82A1|'
                   'Chainsaw|Cluster Grenades|Combat Knife|Desert Eagles|FN Minimi|Grenade|Hands|HK MP5|LAW|M79|Ruger '
                   '77|Selfkill|Spas-12|Stationary gun|Steyr AUG|USSOCOM|XM214 Minigun)\n', contents)
    for kill in m:
      timestamp, killer, victim, weapon = map(string.strip, kill)
      suicide = killer == victim or weapon == 'Selfkill'

      date = parser.parse(timestamp, parser.parserinfo(yearfirst=True))

      if retention.too_old(date):
        continue

      unixtime = int(time.mktime(date.timetuple()))
      yield Kill(
          killer,
          victim,
          weapon,
          unixtime,
          suicide
      )


def update_kills(r, keys, retention, soldat_dir):
  for kill in get_kills(r, keys, retention, soldat_dir):
    apply_kill(r, keys, kill)


def apply_kill(r, keys, kill, incr=1):

  # Add kill to global kill log
  if incr == 1:
    r.lpush(keys.kill_log, pickle.dumps(kill))

  # Stuff that only makes sense for non suicides
  if not kill.suicide:
    r.zincrby(keys.top_players, kill.killer, incr)
    r.hincrby(keys.player_hash(kill.killer), 'kills', incr)

  # Increment number of deaths for victim
  r.hincrby(keys.player_hash(kill.victim), 'deaths', incr)

  # Update first/last time we saw player
  if incr == 1:
    r.hsetnx(keys.player_hash(kill.killer), 'firstseen', kill.timestamp)
    r.hset(keys.player_hash(kill.killer), 'lastseen', kill.timestamp)

  # Update first/last time we saw victim, if they're not the same..
  if incr == 1 and not kill.suicide:
    r.hsetnx(keys.player_hash(kill.victim), 'firstseen', kill.timestamp)
    r.hset(keys.player_hash(kill.victim), 'lastseen', kill.timestamp)

  # Update weapon stats..
  if not kill.suicide:
    r.zincrby(keys.top_weapons, kill.weapon)
    r.hincrby(keys.player_hash(kill.killer), 'kills:' + kill.weapon, incr)
    r.hincrby(keys.player_hash(kill.victim), 'deaths:' + kill.weapon, incr)

  # If we're not a suicide, update top enemy kills for player..
  if not kill.suicide:
    # Top people the killer has killed
    r.zincrby(keys.player_top_enemies(kill.killer), kill.victim, incr)

    # Top people the victim has died by
    r.zincrby(keys.player_top_victims(kill.victim), kill.killer, incr)

  # If we're not a sucide, add this legit kill to the number of kills for this
  # day
  if not kill.suicide:
    text_today = str(datetime.utcfromtimestamp(kill.timestamp).date())
    r.incr(keys.kills_per_day(text_today), incr)
