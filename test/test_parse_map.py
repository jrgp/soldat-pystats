from piestats.update.pms_parser import PmsReader
import os


def test_parse_map():
  map_filename = 'maps/ctf_Ash.pms'

  map_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), map_filename)

  reader = PmsReader()

  with open(map_path, 'rb') as h:
    reader.parse(h)

  assert reader.name == 'ctf_Ash by chakapoko maker'
  assert reader.texture == 'riverbed.bmp'
