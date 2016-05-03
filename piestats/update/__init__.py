from piestats.update.manageevents import ManageEvents
from piestats.update.parseevents import ParseEvents


def update_events(r, keys, retention, filemanager):

  # Get kills and events out of our logs
  parse = ParseEvents(retention, filemanager)

  # Interact with redis to store and delete kills and events
  manage = ManageEvents(r, keys)

  for event in parse.get_events():
    if event:
      manage.apply_event(event)
