import ctypes
from .color import T_Color


class T_Vertex(ctypes.Structure):
  _pack_ = 1
  _fields_ = [
      ('x', ctypes.c_float),
      ('y', ctypes.c_float),
      ('z', ctypes.c_float),
      ('rhw', ctypes.c_float),
      ('color', T_Color),
      ('tu', ctypes.c_float),
      ('tv', ctypes.c_float),
  ]


class T_Vector(ctypes.Structure):
  _pack_ = 1
  _fields_ = [
      ('x', ctypes.c_float),
      ('y', ctypes.c_float),
      ('z', ctypes.c_float),
  ]


class T_Polygon(ctypes.Structure):
  _pack_ = 1
  _fields_ = [
      ('Vertexes', T_Vertex * 3),
      ('Vectors', T_Vector * 3),
      ('Type', ctypes.c_ubyte)
  ]
