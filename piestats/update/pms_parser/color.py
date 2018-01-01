from __future__ import division
import ctypes


class T_Color(ctypes.Structure):
  _pack_ = 1
  _fields_ = [
      ('blue', ctypes.c_ubyte),
      ('green', ctypes.c_ubyte),
      ('red', ctypes.c_ubyte),
      ('alpha', ctypes.c_ubyte),
  ]

  @property
  def for_gl_color(self):
    return [self.__getattribute__(key) / 255 for key in 'red', 'green', 'blue', 'alpha']
