import re
import time
from piestats.models.events import EventPlayerJoin, EventNextMap, EventScore
from piestats.models.kill import Kill
from dateutil import parser


class ParseEvents():

  def __init__(self, retention, filemanager):
    self.retention = retention
    self.filemanager = filemanager

  def parse_events(self, contents):

    kill_regex = '(?P<date>\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d) \(\d\) (?P<killer>.+) killed \(\d\) (?P<victim>.+) ' \
                 'with (?P<weapon>Ak-74|Barrett M82A1|Chainsaw|Cluster Grenades|Combat Knife|Desert Eagles|' \
                 'FN Minimi|Grenade|Hands|HK MP5|LAW|M79|Ruger 77|Selfkill|Spas-12|Stationary gun|Steyr AUG' \
                 '|USSOCOM|XM214 Minigun)'

    header = '\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d '
    event_regexen = [
        (EventPlayerJoin, re.compile(''.join([header, '(?P<player>.+) joining game \((?P<ip>[^:]+):\d+\) HWID:\S+']))),
        (EventNextMap, re.compile(''.join([header, 'Next map: (?P<map>[^$]+)']))),
        (EventScore, re.compile(''.join([header, '(?P<player>.+) scores for (?P<team>Alpha|Bravo) Team$']))),
        (self.generate_kill, re.compile(kill_regex))
    ]

    for line in contents.splitlines():
      for event, regex in event_regexen:
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
    date = parser.parse(kwargs['date'], parser.parserinfo(yearfirst=True))
    unixtime = int(time.mktime(date.timetuple()))

    if self.retention.too_old(date):
      return None

    return Kill(kwargs['killer'], kwargs['victim'], kwargs['weapon'], unixtime)
