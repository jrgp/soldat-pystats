import ctypes


class T_Scenery(ctypes.Structure):
  _pack_ = 1
  _fields_ = [
      ('length', ctypes.c_ubyte),
      ('text', ctypes.c_char * 50),
      ('timestamp', ctypes.c_uint32)
  ]

  @property
  def filename(self):
    return self.__getattribute__('text')[:self.__getattribute__('length')]
