from struct import unpack

from .header import T_Header
from .prop import T_Prop
from .scenery import T_Scenery
from .polygon import T_Polygon
from .collider import T_Collider
from .spawnpoint import T_Spawnpoint
from .waypoint import T_Waypoint

import logging


class PmsReader(object):
  '''
    Parse a Soldat pms map file.
    -
    All of this code is my own, using the PMS map structure guide at the devs
    wiki as a reference for the structures.
  '''

  def __init__(self):
    self.props = []
    self.sceneries = {}
    self.polygons = []
    self.colliders = []
    self.spawnpoints = []
    self.waypoints = []
    self.min_x = 0
    self.max_x = 0
    self.min_y = 0
    self.max_y = 0
    self.header = None

  def _get_long(self, handle):
    # The < is the equivalent of __pack__=1 in our structures, to
    # make it load the packed data properly.
    return unpack('<l', handle.read(4))[0]

  def parse(self, h):
    # Map file header
    self.header = T_Header()
    if not h.readinto(self.header):
      logging.error('Failed reading header')
      return

    logging.info('read header. now reading polys')

    # All polygons
    for i in range(self.header.PolyCount):
      polygon = T_Polygon()
      if not h.readinto(polygon):
        logging.error('Failed reading polygon #{}'.format(i))
        return
      self.polygons.append(polygon)

    logging.info('read polys now doing sector stuff')

    # Skip sector data we don't immediately care about
    sector_division = self._get_long(h)
    num_sectors = self._get_long(h)
    for i in range(((num_sectors * 2) + 1) * ((num_sectors * 2) + 1)):
      sector_polys = unpack('H', h.read(2))[0]
      for j in range(sector_polys):
        h.read(2)

    self.min_x = sector_division * -num_sectors
    self.min_y = sector_division * -num_sectors
    self.max_x = sector_division * num_sectors
    self.max_y = sector_division * num_sectors

    logging.info('read sectors now reading props')

    # All props (scenery placements)
    prop_count = self._get_long(h)
    for i in range(prop_count):
      prop = T_Prop()
      if not h.readinto(prop):
        logging.error('Failed reading prop #{}'.format(i))
        return
      self.props.append(prop)

    logging.info('read props now reading sceneries')

    # All sceneries (map prop style to scenery filename)
    scenery_count = self._get_long(h)
    for i in range(scenery_count):
      scenery = T_Scenery()
      if not h.readinto(scenery):
        logging.error('Failed reading scenery #{}'.format(i))
        return
      self.sceneries[i + 1] = scenery

    logging.info('read sceneries now reading colliders')

    # Colliders
    collider_count = self._get_long(h)
    for i in range(collider_count):
      collider = T_Collider()
      if not h.readinto(collider):
        logging.error('Failed reading collider #{}'.format(i))
        return
      self.colliders.append(collider)

    logging.info('read colliders now reading spawns')

    # Spawnpoints
    spawnpoint_count = self._get_long(h)
    for i in range(spawnpoint_count):
      spawnpoint = T_Spawnpoint()
      if not h.readinto(spawnpoint):
        logging.error('Failed reading spawnpoint #{}'.format(i))
        return
      self.spawnpoints.append(spawnpoint)

    logging.info('read spawns now reading waypoints')

    # Waypoints
    waypoint_count = self._get_long(h)

    for i in range(waypoint_count):
      waypoint = T_Waypoint()
      if not h.readinto(waypoint):
        logging.error('Failed reading waypoint #{}'.format(i))
        return
      self.waypoints.append(waypoint)

    logging.info('read waypoints')

  @property
  def name(self):
    return self.header.Name.name()

  @property
  def texture(self):
    return self.header.Texture.filename()

  def write(self):
    pass
