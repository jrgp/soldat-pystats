import click
from time import time
from datetime import datetime, timedelta
from piestats.update.applyevents import ApplyEvents
from piestats.update.parseevents import ParseEvents
from piestats.models.kill import Kill
from piestats.update.hwid import Hwid


class Retention:
  def __init__(self, r, keys, config, server):
    self.max_days = config.data_retention
    self.keys = keys
    self.r = r
    self.server = server
    self.oldest_allowed_unix = time() - (self.max_days * 86400)
    self.oldest_allowed_datetime = datetime.now() - timedelta(days=self.max_days)
    self.apply_events = ApplyEvents(r=r, keys=keys, hwid=Hwid(r=r, keys=keys), geoip=None)

  def too_old(self, date):
    return self.oldest_allowed_datetime > date

  def too_old_unix(self, seconds):
    return self.oldest_allowed_unix > seconds

  def too_old_filename(self, filename):
    seconds = ParseEvents.get_time_out_of_filename(filename)
    return self.oldest_allowed_unix > seconds

  def run_retention(self):
    '''
      Periodically remove old kills, to save space and ignore old relevant stats.
    '''
    kill_ids = self.r.zrangebyscore(self.keys.kill_log, -1, self.oldest_allowed_unix)

    print('Processing retention.. trimming events up until %s' % datetime.utcfromtimestamp(self.oldest_allowed_unix))

    if not kill_ids:
      return

    with click.progressbar(kill_ids,
                           show_eta=False,
                           label='Killing %d kills' % len(kill_ids),
                           item_show_func=lambda item: 'Kill ID %s' % item if item else '') as progressbar:

      for kill_id in progressbar:
        kill_data = self.r.hget(self.keys.kill_data, kill_id)
        if kill_data:
          kill = Kill.from_redis(kill_data)
        else:
          kill = None
        self.apply_events.rollback_kill(kill, kill_id)
