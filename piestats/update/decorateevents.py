from piestats.models.events import (EventPlayerJoin, EventNextMap, EventScore, EventInvalidMap, EventRequestMap,
                                    EventBareLog, EventRestart, EventShutdown, DecoratedEvent)
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
    # Have we seen this logfile before? If so, maybe we can start from where we left off
    # if there was a round in session
    last_incomplete_round = round_manager.get_old_round_for_log(logfile)
    if last_incomplete_round:
      round_id = last_incomplete_round.id
      current_map = last_incomplete_round.map

    # Or maybe the file which came before this is old and this is a continuation of that
    else:
      last_round_from_last_file = round_manager.get_last_round_from_last_file(logfile)
      if last_round_from_last_file:
        if not last_round_from_last_file.finished:
          round_id = last_round_from_last_file.id
          current_map = last_round_from_last_file.map

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

    elif t == EventInvalidMap and requested_map is not None and requested_map == event.map:
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

    elif t == EventShutdown:
      if round_manager and round_id:
        round_manager.finalize_round(round_id, event.date)

      round_id = None
      current_map = None
      requested_map = None

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
