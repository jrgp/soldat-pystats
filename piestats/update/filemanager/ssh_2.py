from piestats.update.filemanager import FileManager
from contextlib import contextmanager
from fnmatch import fnmatch
from io import BytesIO
import socket
import os
import click

import ssh2.sftp
import ssh2.session


class Ssh2FileManager(FileManager):

  def __init__(self, r, keys, root, retention, connect_settings):
    self.r = r
    self.keys = keys
    self.root = root
    self.retention = retention
    self.sftp = None
    self.connect_settings = connect_settings
    self.init_stats()

  def get_file_paths(self, sub_path, pattern='*'):
    result = []
    handle = self.sftp.opendir(os.path.join(self.root, sub_path))
    for (number, filename, attributes) in handle.readdir():
      if pattern != '*' and not fnmatch(filename, pattern):
        continue
      result.append(os.path.join(self.root, sub_path, filename))
    handle.close()
    return sorted(result)

  def get_paths_with_size(self, sub_path, pattern='*'):
    ''' List of tuples of (path, size) '''
    result = []
    handle = self.sftp.opendir(os.path.join(self.root, sub_path))
    for (number, filename, attributes) in handle.readdir():
      if pattern != '*' and not fnmatch(filename, pattern):
        continue
      result.append((os.path.join(self.root, sub_path, filename), attributes.filesize))
    handle.close()
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
    result = BytesIO()
    handle = self.sftp.open(path, ssh2.sftp.LIBSSH2_FXF_READ, ssh2.sftp.LIBSSH2_SFTP_S_IRUSR)
    handle.seek64(position)
    for size, data in handle:
      if size:
        result.write(data)
    handle.close()
    return result.getvalue()

  @contextmanager
  def initialize(self):

    # Deal with configs. Paramiko does this for us but ssh2 doesn't.
    hostname = self.connect_settings.get('hostname')
    port = int(self.connect_settings.get('port', 22))

    if not hostname:
      raise Exception('Hostname for ssh not specified')

    # Low level TCP connection to ssh server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((hostname, port))

    # Handshake ssh2 connection
    session = ssh2.session.Session()
    session.handshake(sock)

    # Try logging in
    self.attempt_auth(session)

    # Open SFTP channel
    self.sftp = session.sftp_init()

    yield

    # Tear down
    session.disconnect()
    sock.close()

  def filename_key(self, filename):
    return 'ssh://{username}@{hostname}:{port}/{filename}'.format(
        filename=filename,
        username=self.connect_settings.get('username'),
        hostname=self.connect_settings.get('hostname'),
        port=self.connect_settings.get('port'))

  def attempt_auth(self, session):
    ''' Try logging in, supporting some of the common config keys paramiko supports. The first one that works wins '''
    username = self.connect_settings.get('username')
    password = self.connect_settings.get('password')
    key_filename = self.connect_settings.get('key_filename')
    key_passphrase = self.connect_settings.get('passphrase', '')

    failed_types = {}

    # Simple password auth
    if password:
      try:
        session.userauth_password(username, password)
      except Exception as e:
        failed_types['password'] = e
      else:
        print 'SSH login with password successful'
        return

    # Use an ssh agent
    if self.connect_settings.get('allow_agent'):
      try:
        session.agent_auth(username)
      except Exception as e:
        failed_types['agent'] = e
      else:
        print 'SSH login with agent successful'
        return

    # Manually specify path to private keyfile
    if key_filename:
      try:
        session.userauth_publickey_fromfile(username, key_filename, key_passphrase)
      except Exception as e:
        failed_types['key_filename'] = e
      else:
        print 'SSH login with key successful'
        return

    # Try to find keyfiles
    if self.connect_settings.get('look_for_keys'):
      try:
        privkey_files = self.find_privkeys()
        if not privkey_files:
          raise Exception('No private keys found')
        success = False
        for path in privkey_files:
          session.userauth_publickey_fromfile(username, path, key_passphrase)
          success = True
        if not success:
          raise Exception('Failed authing using these privkeys: %s' % ', '.join(privkey_files))
      except Exception as e:
        failed_types['keys'] = e
      else:
        print 'SSH login with found key successful'
        return

    # If we're here, we failed

    if failed_types:
      print 'We failed to authenticate to ssh. Methods we tried:'
      for reason in failed_types.iteritems():
        print 'Option %s failed because: %s' % reason
      raise Exception()
    else:
      raise Exception('Unsure what auth to use. Specify at least one of: password/allow_agent/password/look_for_keys')

  @classmethod
  def find_privkeys(self):
    ''' Try to find all private key files that might be viable '''

    # Partly ripped from https://github.com/paramiko/paramiko/blob/master/paramiko/client.py#L703
    key_types = ('rsa', 'dsa', 'ecdsa', 'ed25519')
    key_dirs = ('~/.ssh', '~/ssh')

    result = []

    for key_dir in key_dirs:
      for key_type in key_types:
        path = os.path.join(os.path.expanduser('%s/id_%s' % (key_dir, key_type)))
        if os.path.exists(path):
          result.append(path)

    return result
