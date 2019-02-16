from contextlib import contextmanager
from piestats.update.filemanager import FileManager
import os
import click
from paramiko.client import SSHClient, WarningPolicy
from paramiko.sftp_client import SFTPClient
from fnmatch import fnmatch


class SshFileManager(FileManager):

  def __init__(self, r, keys, root, retention, connect_settings):
    self.r = r
    self.keys = keys
    self.root = root
    self.retention = retention
    self.client = None
    self.ftpclient = None
    self.connect_settings = connect_settings
    self.init_stats()

  def get_file_paths(self, sub_path, pattern='*'):
    return sorted(os.path.join(self.root, sub_path, filename)
                  for filename in self.ftpclient.listdir(os.path.join(self.root, sub_path)) if fnmatch(filename, pattern))

  def get_paths_with_size(self, sub_path, pattern='*'):
    ''' List of tuples of (path, size) '''
    result = []

    for item in self.ftpclient.listdir_attr(os.path.join(self.root, sub_path)):
      if not fnmatch(item.filename, pattern):
        continue
      result.append((os.path.join(self.root, sub_path, item.filename), item.st_size))

    return sorted(result)

  def get_files(self, sub_path, pattern='*'):
    files = self.get_paths_with_size(sub_path, pattern)
    with click.progressbar(files,
                           show_eta=False,
                           label='Parsing {0} logs from ssh'.format(len(files)),
                           item_show_func=self.progressbar_callback) as progressbar:
      for (path, size) in progressbar:
        if self.retention.too_old_filename(os.path.basename(path)):
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
    with self.ftpclient.open(path, 'r') as h:
      h.seek(position)
      return h.read()

  @contextmanager
  def initialize(self):
    with SSHClient() as client:
      self.client = client
      self.client.set_missing_host_key_policy(WarningPolicy())
      self.client.load_system_host_keys()
      self.client.connect(**self.connect_settings)
      with SFTPClient.from_transport(self.client.get_transport()) as ftpclient:
        self.ftpclient = ftpclient
        yield

  def filename_key(self, filename):
    return 'ssh://{username}@{hostname}:{port}/{filename}'.format(
        filename=filename,
        username=self.connect_settings.get('username'),
        hostname=self.connect_settings.get('hostname'),
        port=self.connect_settings.get('port'))
