import yaml
from piestats.models.server import Server
from piestats.exceptions import InvalidServer


class Config():

  def __init__(self, conf_path):
    ''' Pass me path to config file; I'll load usefulness out of it '''
    with open(conf_path, 'r') as h:
      data = yaml.load(h)

      if not isinstance(data, dict):
        raise RuntimeError('Loaded yaml is garbage: {0}'.format(data))

      self.config = data

  @property
  def redis_prefix(self):
    ''' Get global prefix we use with redis '''
    try:
      return self.config['redis_prefix']
    except KeyError:
      return 'pystats'

  @property
  def redis_connect(self):
    ''' Get the kwargs keypairs which will be shoved into redis connect '''
    if isinstance(self.config['redis_connect'], dict):
      return self.config['redis_connect']
    else:
      return {}

  @property
  def flask_run(self):
    ''' Get the kwargs keypairs which will be shoved into redis connect '''
    if 'flask_run' in self.config and isinstance(self.config['flask_run'], dict):
      return self.config['flask_run']
    else:
      return dict(host='0.0.0.0', debug=True)

  @property
  def servers(self):
    ''' Give Server objects, one per our configured servers '''
    servers = []
    for server in self.config['soldat_servers']:
      servers.append(Server(**server))
    return servers

  @property
  def data_retention(self):
    ''' Days of data to keep; defaults to 365 '''
    try:
      return int(self.config['data_retention'])
    except (ValueError, KeyError):
      return 365

  def get_server(self, slug):
    for server in self.servers:
      if server.url_slug == slug:
        return server
    raise InvalidServer()
