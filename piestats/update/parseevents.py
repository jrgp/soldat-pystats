import re
from piestats.models.events import EventPlayerJoin, EventNextMap, EventScore


class ParseEvents():

  def __init__(self, filemanager):
    self.filemanager = filemanager

  def parse_events(self, contents):

    header = '\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d '
    event_regexen = [
        (EventPlayerJoin, re.compile(''.join([header, '(?P<player>.+) joining game \((?P<ip>[^:]+):\d+\) HWID:\S+']))),
        (EventNextMap, re.compile(''.join([header, 'Next map: (?P<map>[^$]+)']))),
        (EventScore, re.compile(''.join([header, '(?P<player>.+) scores for (?P<team>Alpha|Bravo) Team$']))),
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
