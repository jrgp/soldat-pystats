import ctypes
from .constants import T_Spawntype


class T_Spawnpoint(ctypes.Structure):
  _pack_ = 1
  _fields_ = [
      ('Active', ctypes.c_ubyte),
      ('_filler_', ctypes.c_ubyte * 3),
      ('x', ctypes.c_int),
      ('y', ctypes.c_int),
      ('Type', ctypes.c_int),
  ]

  @property
  def TypeText(self):
    return T_Spawntype[self.__getattribute__('Type')]

  def __str__(self):
    return str(self.TypeText)
