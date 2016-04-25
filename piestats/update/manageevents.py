from piestats.models.events import EventPlayerJoin, EventNextMap
from geoip import geolite2
from IPy import IP


class ManageEvents():
  def __init__(self, r, keys):
    self.r = r
    self.keys = keys

  def apply_event(self, event):
    if isinstance(event, EventPlayerJoin):
      self.update_country(event.ip, event.player)
    elif isinstance(event, EventNextMap):
      self.update_map(event.map)

  def update_country(self, ip, player):
    if not self.r.exists(self.keys.player_hash(player)):
      return
    if IP(ip).iptype() != 'PUBLIC':
      return
    match = geolite2.lookup(ip)
    if not match:
      return
    country_code = match.country
    if self.r.hset(self.keys.player_hash(player), 'lastcountry', country_code):
      self.r.zincrby(self.keys.top_countries, country_code)

  def update_map(self, map):
    self.r.zincrby(self.keys.top_maps, map)
