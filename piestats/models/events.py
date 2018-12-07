from collections import namedtuple
EventPlayerJoin = namedtuple('EventPlayerJoin', ['player', 'ip', 'hwid', 'date'])
EventNextMap = namedtuple('EventNextMap', ['map', 'date'])
EventRequestMap = namedtuple('EventRequestMap', ['map', 'date'])
EventInvalidMap = namedtuple('EventInvalidMap', ['map'])
EventScore = namedtuple('EventScore', ['player', 'team', 'date'])
EventBareLog = namedtuple('EventBareLog', ['line', 'date'])
MapList = namedtuple('MapsList', ['maps', 'score_maps'])
