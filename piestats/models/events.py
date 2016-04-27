from collections import namedtuple
EventPlayerJoin = namedtuple('EventPlayerJoin', ['player', 'ip'])
EventNextMap = namedtuple('EventNextMap', ['map'])
EventScore = namedtuple('EventScore', ['player', 'team'])
