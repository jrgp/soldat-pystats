import logging


class Server:
  def __init__(self, **info):
    self.info = info

  @property
  def dirs(self):
    return self.info['dirs']

  @property
  def redis_key_prefix(self):
    return self.info['slug']

  @property
  def url_slug(self):
    return self.info['slug']

  @property
  def title(self):
    return self.info['title']

  @property
  def admin_details(self):
    keys = ['ip', 'port', 'password']

    # Don't output warning message if we have none of the server stats keys,
    # which pretty much means the user doesn't want them.
    if all(key not in self.info for key in keys):
      return None

    for key in keys:
      if key not in self.info:
        logging.warning('Missing key %s needed for admin connection', key)
        return None
      if str(self.info[key]) == '':
        logging.warning('Empty key %s needed for admin connection', key)
        return None

    try:
      self.info['port'] = int(self.info['port'])
    except ValueError:
      logging.warning('Admin port specified %s not a number', self.info['port'])
      return None

    return {k: self.info[k] for k in keys}

  @property
  def log_source(self):
    options = ('local', 'ssh', 'ftp')
    given = self.info.get('source', None)
    if given in options:
      return given
    return 'local'

  @property
  def connection_options(self):
    if 'connection' in self.info and isinstance(self.info['connection'], dict):
      return self.info['connection']
    else:
      return dict()
