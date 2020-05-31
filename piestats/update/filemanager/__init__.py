from contextlib import contextmanager
from collections import deque
from time import time


class FileManager():

  def __init__(self):
    raise NotImplementedError

  def get_file_paths(self):
    raise NotImplementedError

  def get_files(self):
    raise NotImplementedError

  def get_data(self):
    raise NotImplementedError

  def filename_key(self):
    raise NotImplementedError

  @contextmanager
  def initialize(self):
    yield

  def init_stats(self):
    self.last_log_times = deque(maxlen=20)
    self.time_since_last = 0

  def progressbar_callback(self, item):
    if item:
        time_stat = ''
        now = time()
        if self.time_since_last:
          self.last_log_times.append(now - self.time_since_last)
          time_stat = ' (%.2fs per log)' % (sum(self.last_log_times) / len(self.last_log_times))
        self.time_since_last = now

        # sometimes the item is a tuple with the first elem being the name and the rest
        # being helpful metadata for the filemanager
        if isinstance(item, tuple):
          item = item[0]

        return 'Parsing %s%s' % (item, time_stat)
