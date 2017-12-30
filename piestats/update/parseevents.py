import re
import time
from piestats.models.events import EventPlayerJoin, EventNextMap, EventScore
from piestats.models.kill import Kill
from dateutil import parser


class ParseEvents():

  def __init__(self, retention, filemanager):
    self.retention = retention
    self.filemanager = filemanager
    self.parse_kill_date_parserinfo = parser.parserinfo(yearfirst=True)

    kill_regex = ('(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) \(\d\) (?P<killer>.+) killed \(\d\) (?P<victim>.+) '
                  'with (?P<weapon>Ak-74|Barrett M82A1|Chainsaw|Cluster Grenades|Combat Knife|Desert Eagles|'
                  'FN Minimi|Grenade|Hands|HK MP5|LAW|M79|Ruger 77|Selfkill|Spas-12|Stationary gun|Steyr AUG'
                  '|USSOCOM|XM214 Minigun|Bow|Flame Bow)')

    self.event_regex = (
        (EventPlayerJoin, re.compile('\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d (?P<player>.+) joining game \((?P<ip>[^:]+):\d+\) HWID:\S+')),
        (EventNextMap, re.compile('\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d Next map: (?P<map>[^$]+)')),
        (EventScore, re.compile('\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d (?P<player>.+) scores for (?P<team>Alpha|Bravo) Team$')),
        (self.generate_kill, re.compile(kill_regex)),
    )

  def parse_events(self, contents):
    for line in contents.splitlines():
      for event, regex in self.event_regex:
        m = regex.match(line.strip())
        if not m:
          continue
        yield event(**m.groupdict())

  def get_events(self):
    '''
      Get all events from relevant console log files
    '''
    for path, position in self.filemanager.get_files('logs', 'consolelog*.txt'):
      for event in self.parse_events(self.filemanager.get_data(path, position)):
        yield event

  def generate_kill(self, *args, **kwargs):
    date = parser.parse(kwargs['date'], self.parse_kill_date_parserinfo)

    if self.retention.too_old(date):
      return None

    if kwargs['weapon'] == 'Flame Bow':
      kwargs['weapon'] = 'Bow'

    return Kill(kwargs['killer'], kwargs['victim'], kwargs['weapon'], int(time.mktime(date.timetuple())))
