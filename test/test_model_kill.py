from piestats.models.kill import Kill
from datetime import datetime


def test_type():
  k = Kill('Major', 'Major', 'HK MP5', 0)
  assert k.suicide is True

  k = Kill('Major', 'Zombie', 'HK MP5', 0)
  assert k.suicide is False


def test_teams():
  k = Kill('Terminator', 'Major', 'HK MP5', 0, killer_team=1, victim_team=2)
  assert k.killer_team == 'alpha'
  assert k.victim_team == 'bravo'

  k = Kill('Terminator', 'Major', 'HK MP5', 0)
  assert k.killer_team is None
  assert k.victim_team is None


def test_equality():
  k1 = Kill('Terminator', 'Major', 'HK MP5', 0, killer_team=1, victim_team=2)
  k2 = Kill('Terminator', 'Major', 'HK MP5', 0, killer_team=1, victim_team=2)

  assert k1 == k2


def test_serializing():
  k1 = Kill('Terminator', 'Major', 'HK MP5', 0, killer_team=1, victim_team=2)

  assert Kill.from_tuple(k1.to_tuple()) == k1
  assert Kill.from_redis(k1.to_redis()) == k1


def test_dates():
  k = Kill('Major', 'Major', 'HK MP5', 0)
  assert isinstance(k.datetime, datetime)
