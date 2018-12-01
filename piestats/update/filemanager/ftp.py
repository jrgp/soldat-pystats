from contextlib import contextmanager
from piestats.update.filemanager import FileManager
import os
import logging
import click
from fnmatch import fnmatch
from io import BytesIO
import ftplib


class FtpFileManager(FileManager):

  def __init__(self, r, keys, root, retention, connect_settings):
    self.r = r
    self.keys = keys
    self.root = root
    self.retention = retention
    self.connect_settings = connect_settings
    self.ftp = None
    self.init_stats()

  def get_file_paths(self, sub_path, pattern='*'):
    if not self.ftp:
      return []

    return sorted(os.path.join(self.root, sub_path, filename) for filename in self.ftp.nlst(os.path.join(self.root, sub_path)) if fnmatch(filename, pattern))

  def get_files(self, sub_path, pattern='*'):
    if not self.ftp:
      return

    files = self.get_file_paths(sub_path, pattern)

    with click.progressbar(files,
                           show_eta=False,
                           label='Parsing {0} logs from ftp'.format(len(files)),
                           item_show_func=self.progressbar_callback) as progressbar:
      for path in progressbar:
        if self.retention.too_old_filename(os.path.basename(path)):
          continue

        try:
          size = self.ftp.size(path)
        except ftplib.error_perm:
          continue

        key = self.filename_key(path)
        prev = self.r.hget(self.keys.log_positions, key)
        if prev is None:
          pos = 0
        else:
          pos = int(prev)

        if size > pos:
          if progressbar.is_hidden:
            print('Reading {filename} from offset {pos}'.format(filename=path, pos=pos))
          yield path, pos
          self.r.hset(self.keys.log_positions, key, size)

  def get_data(self, path, position):
    data = BytesIO()
    self.ftp.retrbinary('RETR %s' % path, data.write)
    data.seek(position, 0)
    return data.getvalue()

  @contextmanager
  def initialize(self):
    try:
      self.ftp = ftplib.FTP()
      self.ftp.connect(self.connect_settings['hostname'], int(self.connect_settings['port']))
      self.ftp.login(self.connect_settings['username'], self.connect_settings['password'])
    except ftplib.error_perm as e:
      logging.error('Accessing FTP failed: %s', e)
      self.ftp = None

    yield

    if self.ftp:
      self.ftp.close()

  def filename_key(self, filename):
    return 'ftp://{username}@{hostname}:{port}/{filename}'.format(
        filename=filename,
        username=self.connect_settings['username'],
        hostname=self.connect_settings['hostname'],
        port=self.connect_settings['port'])
