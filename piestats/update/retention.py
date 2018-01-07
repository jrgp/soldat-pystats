import click
from time import time
from datetime import datetime
from piestats.update.manageevents import ManageEvents
from piestats.models.kill import Kill


class Retention:
  def __init__(self, r, keys, config):
    self.max_days = config.data_retention
    self.keys = keys
    self.r = r
    self.manage = ManageEvents(r, keys)

  def too_old(self, date):
    return (datetime.now() - date).days > self.max_days

  def run_retention(self):
    '''
      Periodically remove old kills, to save space and ignore old relevant stats.
    '''
    oldest_allowed = time() - (self.max_days * 86400)

    kill_ids = self.r.zrangebyscore(self.keys.kill_log, -1, oldest_allowed)

    print 'Processing retention.. trimming events up until %s' % datetime.utcfromtimestamp(oldest_allowed)

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
        self.manage.rollback_kill(kill, kill_id)
