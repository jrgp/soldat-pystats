class PystatsServer:
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
