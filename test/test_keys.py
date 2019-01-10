from piestats.keys import Keys
import unittest


class FakeServer():
    redis_key_prefix = 'server1'


class FakeConfig():
    redis_prefix = 'pystats'


class TestKeys(unittest.TestCase):
  def test_keys(self):
      k = Keys(FakeConfig(), FakeServer())

      assert k.top_players == 'pystats:server1:top_players'
      assert k.player_search == 'pystats:server1:player_search'
      assert k.kill_log == 'pystats:server1:kill_log'
      assert k.top_weapons == 'pystats:server1:top_weapons'
      assert k.top_countries == 'pystats:server1:top_countries'
      assert k.top_maps == 'pystats:server1:top_maps'
      assert k.kills_per_day('2016-10-30') == 'pystats:server1:kills_per_day:2016-10-30'
      assert k.player_hash('jrgp') == 'pystats:server1:player:jrgp'
      assert k.player_top_enemies('jrgp') == 'pystats:server1:player_top_enemies:jrgp'
      assert k.player_top_victims('jrgp') == 'pystats:server1:player_top_victims:jrgp'
      assert k.weapon_top_killers('HK MP5') == 'pystats:server1:weapon_top_killers:HK MP5'


if __name__ == '__main__':
  unittest.main()
