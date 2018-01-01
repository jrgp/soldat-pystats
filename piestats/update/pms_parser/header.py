import ctypes
from .color import T_Color


class T_Name(ctypes.Structure):
  _pack_ = 1
  _fields_ = [('length', ctypes.c_ubyte), ('text', ctypes.c_char * 38)]

  def name(self):
    return self.__getattribute__('text')[:self.__getattribute__('length')]


class T_Texture(ctypes.Structure):
  _pack_ = 1
  _fields_ = [('length', ctypes.c_ubyte), ('text', ctypes.c_char * 24)]

  def filename(self):
    return self.__getattribute__('text')[:self.__getattribute__('length')]


class T_Header(ctypes.Structure):
  _pack_ = 1
  _fields_ = [
      ('Version', ctypes.c_uint32),
      ('Name', T_Name),
      ('Texture', T_Texture),
      ('BackgroundColorTop', T_Color),
      ('BackgroundColorBottom', T_Color),
      ('Jets', ctypes.c_uint32),
      ('Grenades', ctypes.c_byte),
      ('Medkits', ctypes.c_ubyte),
      ('Weather', ctypes.c_ubyte),
      ('Steps', ctypes.c_ubyte),
      ('RandId', ctypes.c_uint32),
      ('PolyCount', ctypes.c_uint32),
  ]
