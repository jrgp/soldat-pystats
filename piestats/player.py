class PlayerObj():

  def __init__(self, name):
    self._name = name

  @property
  def name(self):
    return self._name

  @property
  def data_key(self):
    return 'pystats:playerdata:{name}'.format(name=self.name)

  def __str__(self):
    return self.name
