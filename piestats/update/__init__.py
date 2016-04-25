from piestats.update.managekills import ManageKills
from piestats.update.parsekills import ParseKills
from piestats.update.filemanager.local import LocalFileManager
import os


def update_kills(r, keys, retention, soldat_dir):

  # Interface to local kill log files, storing position in redis
  filemanager = LocalFileManager(r, keys, os.path.join(soldat_dir, 'logs/kills'))

  # Get kills out of our logs
  parse = ParseKills(retention, filemanager)

  # Interact with redis to store and delete kills
  manage = ManageKills(r, keys)

  for kill in parse.get_kills():
    manage.apply_kill(kill)
