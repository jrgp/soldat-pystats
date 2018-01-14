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
    return sorted(filter(lambda x: fnmatch(x, pattern), self.ftpclient.listdir(os.path.join(self.root, sub_path))))

  def get_files(self, sub_path, pattern='*'):
    files = self.get_file_paths(sub_path, pattern)
    with click.progressbar(files,
                           show_eta=False,
                           label='Parsing {0} logs from ssh'.format(len(files)),
                           item_show_func=self.progressbar_callback) as progressbar:
      for filename in progressbar:
        path = os.path.join(self.root, sub_path, filename)
        size = self.ftpclient.lstat(path).st_size
        key = self.keys.log_file(filename='ssh://' + path)
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
