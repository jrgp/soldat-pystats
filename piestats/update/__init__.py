import redis
from piestats.update.kills import update_kills
from piestats.update.events import update_events


def main():
  soldat_dir = '/root/pyredis_stats/soldat'
  r = redis.Redis()
  update_kills(r, soldat_dir)
  update_events(r, soldat_dir)
