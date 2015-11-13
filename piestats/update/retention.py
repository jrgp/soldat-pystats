import datetime
from piestats.update.kills import apply_kill

try:
  import cPickle as pickle
except ImportError:
  import pickle


class PystatsRetention:
  def __init__(self, config, keys, r):
    self.max_days = config.data_retention
    self.keys = keys
    self.r = r

  def too_old(self, date):
    return (datetime.datetime.now() - date).days > self.max_days

  def run_retention(self):
    limit = str(datetime.datetime.now() - datetime.timedelta(days=self.max_days)).split('.')[0]
    print 'Processing retention.. trimming events up until {limit}'.format(limit=limit)
    for index, kill in self.iterate_backwards():
      timestamp = datetime.datetime.utcfromtimestamp(int(kill.timestamp))
      if not self.too_old(timestamp):
        break
      self.undo_kill(kill)

  def undo_kill(self, kill):
    '''
      Reverse the actions of a kill. Decrement counters/etc
    '''

    apply_kill(self.r, self.keys, kill, -1)

    text_today = str(datetime.datetime.utcfromtimestamp(kill.timestamp).date())
    self.r.delete(self.keys.kills_per_day(text_today))

    self.r.rpop(self.keys.kill_log)

    print 'killed {0}'.format(kill)

  def iterate_backwards(self):
    '''
      Work through kill log backwards, yielding each kill object along with index
    '''
    try:
      num_kills = int(self.r.llen(self.keys.kill_log))
    except ValueError:
      print 'no kills?'
      return

    i = num_kills

    while i > 0:
      index = i - 1
      i -= 1
      this_kill = self.r.lindex(self.keys.kill_log, index)
      if this_kill is None:
        print 'none kill?'
        break
      data = pickle.loads(this_kill)
      yield index, data
