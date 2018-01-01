import ctypes


class T_Collider(ctypes.Structure):
  _pack_ = 1
  _fields_ = [
      ('Active', ctypes.c_ubyte),
      ('_filler_', ctypes.c_ubyte * 3),
      ('x', ctypes.c_float),
      ('y', ctypes.c_float),
      ('Radius', ctypes.c_float),
  ]
