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
        logging.warning('Missing key {0} needed for admin connection'.format(key))
        return None
      if str(self.info[key]) == '':
        logging.warning('Empty key {0} needed for admin connection'.format(key))
        return None

    try:
      self.info['port'] = int(self.info['port'])
    except ValueError:
      logging.exception('Admin port specified not an int')
      return None

    return {k: self.info[k] for k in keys}
