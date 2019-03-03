from piestats.update.filemanager import FileManager
import os
import glob
import click


class LocalFileManager(FileManager):

  def __init__(self, r, keys, root, retention):
    self.r = r
    self.keys = keys
    self.root = root
    self.retention = retention
    self.init_stats()

  def get_file_paths(self, sub_path, pattern='*'):
    return sorted(glob.glob(os.path.join(self.root, sub_path, pattern)))

  def get_files(self, sub_path, pattern='*'):
    paths = self.get_file_paths(sub_path, pattern)

    with click.progressbar(paths,
                           show_eta=False,
                           label='Parsing {0} local logs'.format(len(paths)),
                           item_show_func=self.progressbar_callback) as progressbar:
      for path in progressbar:
        size = os.path.getsize(path)
        mtime = os.path.getmtime(path)

        # Skip ancient files we have no business wasting time parsing
        if self.retention.too_old_unix(mtime) or self.retention.too_old_filename(os.path.basename(path)):
          continue

        key = self.filename_key(path)
        prev = self.r.hget(self.keys.log_positions, key)
        if prev is None:
          pos = 0
        else:
          pos = int(prev)
        if size > pos:
          if progressbar.is_hidden:
            print(('Reading {filename} from offset {pos}'.format(filename=path, pos=pos)))
          yield path, pos
          self.r.hset(self.keys.log_positions, key, size)

  def get_data(self, path, position):
    with open(path, 'rb') as h:
      h.seek(position)
      return h.read()

  def filename_key(self, filename):
    return 'local:%s' % filename
