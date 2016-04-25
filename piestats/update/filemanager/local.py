from piestats.update.filemanager import FileManager
import os
import glob
import click


class LocalFileManager(FileManager):

  def __init__(self, r, keys, root, pattern):
    self.r = r
    self.keys = keys
    self.root = root
    self.pattern = pattern

  def get_files(self):
    paths = sorted(glob.glob(os.path.join(self.root, self.pattern)))

    def progress_function(item):
      if item:
        return 'Parsing {0}'.format(item)

    with click.progressbar(paths,
                           show_eta=False,
                           label='Parsing {0} local logs'.format(len(paths)),
                           item_show_func=progress_function) as progressbar:
      for path in progressbar:
        key = self.keys.log_file(filename=path)
        size = os.path.getsize(path)
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
      with open(path, 'r') as h:
        h.seek(position)
        return h.read()
