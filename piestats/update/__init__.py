from piestats.update.managekills import ManageKills
from piestats.update.parsekills import ParseKills
from piestats.update.manageevents import ManageEvents
from piestats.update.parseevents import ParseEvents
from piestats.update.filemanager.local import LocalFileManager
import os


def update_kills(r, keys, retention, soldat_dir):

  # Interface to local kill log files, storing position in redis
  filemanager = LocalFileManager(r, keys, os.path.join(soldat_dir, 'logs/kills'), '*.txt')

  # Get kills out of our logs
  parse = ParseKills(retention, filemanager)

  # Interact with redis to store and delete kills
  manage = ManageKills(r, keys)

  for kill in parse.get_kills():
    manage.apply_kill(kill)


def update_events(r, keys, soldat_dir):

  # Interface to local console log files, storing position in redis
  filemanager = LocalFileManager(r, keys, os.path.join(soldat_dir, 'logs'), 'consolelog*.txt')

  # Get kills out of our logs
  parse = ParseEvents(filemanager)

  # Interact with redis to store and delete kills
  manage = ManageEvents(r, keys)

  for event in parse.get_events():
    manage.apply_event(event)
