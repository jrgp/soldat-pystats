from piestats.models.player import Player


def test_kd():
  p = Player(kills=10, deaths=5)
  assert p.kd == 2

  p = Player(kills=0, deaths=5)
  assert p.kd == 0

  p = Player(kills=10, deaths=0)
  assert p.kd == 10

  p = Player(kills=0, deaths=0)
  assert p.kd == 0

  p = Player(kills=10, deaths=3)
  assert p.kd == 3.33
