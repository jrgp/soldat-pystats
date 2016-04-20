from piestats.update.managekills import ManageKills
from piestats.update.parsekills import ParseKills


def update_kills(r, keys, retention, soldat_dir):

  # Parse soldat logfiles and store position in redis
  parse = ParseKills(r, keys, retention, soldat_dir)

  # Interact with redis to store and delete kills
  manage = ManageKills(r, keys)

  for kill in parse.get_kills():
    manage.apply_kill(kill)
