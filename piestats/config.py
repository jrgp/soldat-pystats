import yaml


class PystatsConfig():

  def __init__(self, conf_path):
    with open(conf_path, 'r') as h:
      data = yaml.load(h)

      if not isinstance(data, dict):
        raise RuntimeError('Loaded yaml is garbage: {0}'.format(data))

      self.config = data

  @property
  def redis_prefix(self):
    try:
      return self.config['redis_prefix']
    except KeyError:
      return 'pystats'

  @property
  def redis_connect(self):
    if isinstance(self.config['redis_connect'], dict):
      return self.config['redis_connect']
    else:
      return {}

  @property
  def soldat_dirs(self):
    return self.config['soldat_dir']

  @property
  def data_retention(self):
    try:
      return int(self.config['data_retention'])
    except (ValueError, KeyError):
      return 365
