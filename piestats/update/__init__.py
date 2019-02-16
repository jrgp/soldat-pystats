from piestats.update.manageevents import ManageEvents
from piestats.update.parseevents import ParseEvents


def update_events(r, keys, retention, filemanager, server):

  # Get kills and events out of our logs
  parse = ParseEvents(retention, filemanager, r, keys)

  # Interact with redis to store and delete kills and events
  with ManageEvents(r, keys, server) as manage:
    for event in parse.get_events():
      if event:
        manage.apply_event(event)
