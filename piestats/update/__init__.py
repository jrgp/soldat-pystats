import redis
from piestats.update.kills import update_kills
from piestats.update.events import update_events


def main():
  r = redis.Redis()
  update_kills(r)
  update_events(r)
