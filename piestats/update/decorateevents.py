from piestats.models.events import EventPlayerJoin, EventNextMap, EventScore, EventInvalidMap, EventRequestMap, EventBareLog, EventRestart, DecoratedEvent
from piestats.models.kill import Kill

# The Soldat gather scripts allow omitting the ctf_ prefix when requesting maps
ctf_prefix = 'ctf_'


def decorate_event(event, map, round_id):
  return DecoratedEvent(event=event, map=map, round_id=round_id)


def decorate_events(events, map_titles=None, ignore_maps=None, ignore_players=None, round_manager=None, logfile=None):
  '''
    State machine to convert raw events from logs to analyzeable events to be saved to and aggregated in redis

    Deliberately a single pure function to make testing possible/easier and to try to reduce external state as much
    as possible.
  '''

  # The only state this function keeps during its run loop
  round_id = None
  requested_map = None
  current_map = None

  if not map_titles:
    map_titles = {}

  if not ignore_maps:
    ignore_maps = tuple()

  if not ignore_players:
    ignore_players = tuple()

  if round_manager and logfile:
    last_incomplete_round = round_manager.get_old_round_for_log(logfile)
    if last_incomplete_round:
      round_id = last_incomplete_round.id
      current_map = last_incomplete_round.map

  for event in events:
    t = type(event)

    if t == EventNextMap or t == EventRequestMap:
      if event.map in map_titles:
        requested_map = event.map
      else:
        if not event.map.startswith(ctf_prefix) and ctf_prefix + event.map in map_titles:
          requested_map = ctf_prefix + event.map
        else:
          requested_map = None

    elif t == EventInvalidMap and requested_map is not None:
      requested_map = None

    elif t == EventBareLog and requested_map is not None:
      if event.line.strip() == map_titles[requested_map]:
        current_map = requested_map
        requested_map = None

        if round_manager:
          if round_id:
            round_manager.finalize_round(round_id, event.date)
            round_id = None

          if current_map not in ignore_maps:
            round_id = round_manager.new_round(current_map, event.date, logfile)

    elif t == EventRestart:
      requested_map = current_map

    else:
      if round_manager and not round_id:
        continue

      if current_map in ignore_maps:
        continue

      if (t == EventScore or t == EventPlayerJoin) and event.player in ignore_players:
        continue

      if isinstance(event, Kill):
        if event.killer in ignore_players or event.victim in ignore_players:
          continue
        else:
          if round_id:
            event.round_id = round_id
          event.map = current_map

      yield decorate_event(event=event, map=current_map, round_id=round_id)
