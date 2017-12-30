import datetime
from piestats.update.manageevents import ManageEvents
from piestats.models.kill import Kill


class Retention:
  def __init__(self, r, keys, config):
    self.max_days = config.data_retention
    self.keys = keys
    self.r = r
    self.manage = ManageEvents(r, keys)

  def too_old(self, date):
    return (datetime.datetime.now() - date).days > self.max_days

  def run_retention(self):
    '''
      Periodically remove old kills, to save space and ignore old relevant stats.
    '''
    limit = str(datetime.datetime.now() - datetime.timedelta(days=self.max_days)).split('.')[0]
    print('Processing retention.. trimming events up until {limit}'.format(limit=limit))
    for kill in self.iterate_backwards():

      if not self.too_old(kill.datetime):
        break
      self.manage.rollback_kill(kill)

  def iterate_backwards(self):
    '''
      Work through kill log backwards, yielding each kill object
    '''
    try:
      num_kills = int(self.r.llen(self.keys.kill_log))
    except ValueError:
      print('no kills?')
      return

    i = num_kills

    while i > 0:
      index = i - 1
      i -= 1
      this_kill = self.r.lindex(self.keys.kill_log, index)
      if this_kill is None:
        print('none kill?')
        break
      data = Kill.from_redis(this_kill)
      yield data
