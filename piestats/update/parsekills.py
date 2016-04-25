from dateutil import parser
from piestats.models.kill import Kill
import re
import string
import time


class ParseKills():

  def __init__(self, retention, filemanager):
    self.retention = retention
    self.filemanager = filemanager

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
    for path, position in self.filemanager.get_files('logs/kills', '*.txt'):
      for kill in self.parse_kills(self.filemanager.get_data(path, position)):
        yield kill
