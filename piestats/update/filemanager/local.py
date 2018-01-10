from piestats.update.filemanager import FileManager
from time import time
import os
import glob
import click


class LocalFileManager(FileManager):

  def __init__(self, r, keys, root, retention):
    self.r = r
    self.keys = keys
    self.root = root
    self.retention = retention

    self.last_log_times = []
    self.time_since_last = 0

  def get_file_paths(self, sub_path, pattern='*'):
    return sorted(glob.glob(os.path.join(self.root, sub_path, pattern)))

  def get_files(self, sub_path, pattern='*'):
    paths = self.get_file_paths(sub_path, pattern)

    def progress_function(item):
      time_stat = ''
      now = time()
      if self.time_since_last:
        time_stat = ' (%.2fs per log)' % self.avg_per_log(now - self.time_since_last)
      self.time_since_last = now

      if item:
        return 'Parsing %s%s' % (item, time_stat)

    with click.progressbar(paths,
                           show_eta=False,
                           label='Parsing {0} local logs'.format(len(paths)),
                           item_show_func=progress_function) as progressbar:
      for path in progressbar:
        key = self.keys.log_file(filename=path)
        size = os.path.getsize(path)
        mtime = os.path.getmtime(path)

        # Skip ancient files we have no business wasting time parsing
        if self.retention.too_old_unix(mtime):
          continue

        prev = self.r.get(key)
        if prev is None:
          pos = 0
        else:
          pos = int(prev)
        if size > pos:
          if progressbar.is_hidden:
            print('Reading {filename} from offset {pos}'.format(filename=path, pos=pos))
          yield path, pos
          self.r.set(key, size)

  def get_data(self, path, position):
    with open(path, 'rb') as h:
      h.seek(position)
      return h.read()

  def avg_per_log(self, this_time):
    self.last_log_times.append(this_time)
    count = len(self.last_log_times)
    if count > 10:
      self.last_log_times.pop(0)
    return sum(self.last_log_times) / count
