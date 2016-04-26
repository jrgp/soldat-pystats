from piestats.update.filemanager import FileManager
import os
import click
from paramiko.client import SSHClient, WarningPolicy
from paramiko.sftp_client import SFTPClient
from fnmatch import fnmatch


class SshFileManager(FileManager):

  def __init__(self, r, keys, root, connect_settings):
    self.r = r
    self.keys = keys
    self.root = root
    self.ftpclient = None
    self.connect_settings = connect_settings

  def get_files(self, sub_path, pattern='*'):
    def progress_function(item):
      if item:
        return 'Parsing {0}'.format(item)

    with SSHClient() as client:
      client.set_missing_host_key_policy(WarningPolicy())
      client.load_system_host_keys()
      client.connect(**self.connect_settings)
      with SFTPClient.from_transport(client.get_transport()) as ftpclient:
        self.ftpclient = ftpclient
        files = sorted(filter(lambda x: fnmatch(x, pattern), ftpclient.listdir(os.path.join(self.root, sub_path))))
        with click.progressbar(files,
                               show_eta=False,
                               label='Parsing {0} logs from ssh'.format(len(files)),
                               item_show_func=progress_function) as progressbar:
          for filename in progressbar:
            path = os.path.join(self.root, sub_path, filename)
            size = ftpclient.lstat(path).st_size
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
