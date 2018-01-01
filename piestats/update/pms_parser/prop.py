import ctypes
from .color import T_Color
from .constants import T_PropLevel


class T_Prop(ctypes.Structure):
  _pack_ = 1
  _fields_ = [
      ('Active', ctypes.c_ubyte),
      ('_filler_1', ctypes.c_ubyte),
      ('Style', ctypes.c_ushort),
      ('Width', ctypes.c_uint32),
      ('Height', ctypes.c_uint32),
      ('x', ctypes.c_float),
      ('y', ctypes.c_float),
      ('Rotation', ctypes.c_float),
      ('ScaleX', ctypes.c_float),
      ('ScaleY', ctypes.c_float),
      ('Alpha', ctypes.c_ubyte),
      ('_filler_2', ctypes.c_ubyte * 3),
      ('Color', T_Color),
      ('Level', ctypes.c_ubyte),
      ('_filler_3', ctypes.c_ubyte * 3),
  ]

  @property
  def LevelText(self):
    return T_PropLevel[self.__getattribute__('Level')]
