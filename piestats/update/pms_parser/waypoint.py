import ctypes


class T_Waypoint(ctypes.Structure):
  _pack_ = 1
  _fields_ = [
      ('Active', ctypes.c_ubyte),
      ('_filler1_', ctypes.c_ubyte * 3),
      ('id', ctypes.c_uint32),
      ('x', ctypes.c_uint32),
      ('y', ctypes.c_uint32),
      ('Left', ctypes.c_ubyte),
      ('Right', ctypes.c_ubyte),
      ('Up', ctypes.c_ubyte),
      ('Down', ctypes.c_ubyte),
      ('Jet', ctypes.c_ubyte),
      ('Path', ctypes.c_ubyte),
      ('SpecialAction', ctypes.c_ubyte),
      ('c2', ctypes.c_ubyte),
      ('c3', ctypes.c_ubyte),
      ('_filler2_', ctypes.c_ubyte * 3),
      ('NumConnections', ctypes.c_uint32),
      ('Connections', ctypes.c_uint32 * 20),
  ]
