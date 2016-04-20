from dateutil import parser
from piestats.models.kill import Kill
import re
import os
import glob
import string
import time


class ParseKills():

  def __init__(self, r, keys, retention, soldat_dir):
    self.r = r
    self.keys = keys
    self.retention = retention
    self.soldat_dir = soldat_dir

  def get_files(self):
    '''
      Get a list of files in our soldat dir and the position we left off last time
    '''
    root = os.path.join(self.soldat_dir, 'logs', 'kills')

    # Make sure we go by filename sorted in ascending order, as we can't sort
    # our global kill log after items are inserted.
    files = sorted(map(os.path.basename, glob.glob(os.path.join(root, '*.txt'))))

    skipped_files = 0

    for filename in files:
      path = os.path.join(root, filename)
      key = self.keys.log_file(filename=path)
      size = os.path.getsize(path)
      prev = self.r.get(key)
      if prev is None:
        pos = 0
      else:
        pos = int(prev)
      if size > pos:
        print('reading {filename} from offset {pos}'.format(filename=filename, pos=pos))
        yield path, pos
        self.r.set(key, size)
      else:
        skipped_files += 1

    print('skipped {count} unchanged kill logs'.format(count=skipped_files))

  def parse_kills(self, contents):
    '''
      Given contents of a kill log, yield all kills within
    '''
    m = re.findall('\-\-\- (\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d)\\n(.+)\\n(.+)\\n(Ak-74|Barrett M82A1|'
                   'Chainsaw|Cluster Grenades|Combat Knife|Desert Eagles|FN Minimi|Grenade|Hands|HK MP5|LAW|M79|Ruger '
                   '77|Selfkill|Spas-12|Stationary gun|Steyr AUG|USSOCOM|XM214 Minigun)\n', contents)
    for match in m:
      timestamp, killer, victim, weapon = map(string.strip, match)

      date = parser.parse(timestamp, parser.parserinfo(yearfirst=True))
      unixtime = int(time.mktime(date.timetuple()))

      if not self.retention.too_old(date):
        yield Kill(killer, victim, weapon, unixtime)

  def get_kills(self):
    '''
      Get all kills from relevant kill log files
    '''
    # For each file we have
    for path, position in self.get_files():
      with open(path, 'r') as h:

        # Start reading from where we left off last time
        h.seek(position)

        # Get all kills inside it
        for kill in self.parse_kills(h.read()):
          yield kill
