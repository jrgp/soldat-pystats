class PlayerObj():

  def __init__(self, name):
    self._name = name

  @property
  def name(self):
    return self._name

  @property
  def data_key(self):
    return 'pystats:playerdata:{name}'.format(name=self.name)

  @property
  def top_enemies_key(self):
    return 'pystats:players:topenemies:{name}'.format(name=self.name)

  @property
  def top_victims_key(self):
    return 'pystats:players:topvictims:{name}'.format(name=self.name)

  def __str__(self):
    return self.name
