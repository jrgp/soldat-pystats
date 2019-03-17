import unittest
import pytest
from piestats.update.parseevents import ParseEvents
from piestats.models.events import EventPlayerJoin, EventNextMap, EventScore, EventInvalidMap, EventRequestMap, EventBareLog, EventShutdown, EventRestart
from piestats.models.kill import Kill


class FakeRetention():
    def too_old(self, x):
        return False


retention = FakeRetention()


class TestParseEvents(unittest.TestCase):

  def test_parse_player_join(self):
    event = ParseEvents(retention, None, None, None).parse_line('15-01-30 23:34:09 rage rage foo rage joining game (84.120.15.45:23073) HWID:4DD3F08B8AA')
    self.assertIsInstance(event, EventPlayerJoin)
    self.assertEqual(event.player, 'rage rage foo rage')
    self.assertEqual(event.ip, '84.120.15.45')
    self.assertEqual(event.hwid, '4DD3F08B8AA')
    self.assertIsInstance(event.date, int)

  def test_parse_next_map(self):
    event = ParseEvents(retention, None, None, None).parse_line('15-02-11 20:37:48 Next map: Blox')
    self.assertIsInstance(event, EventNextMap)
    self.assertEqual(event.map, 'Blox')
    self.assertIsInstance(event.date, int)

  def test_parse_cmd_map(self):
    event = ParseEvents(retention, None, None, None).parse_line('15-02-11 20:37:48 /map ctf_Wretch (198.136.48.50)')
    self.assertIsInstance(event, EventNextMap)
    self.assertEqual(event.map, 'ctf_Wretch')
    self.assertIsInstance(event.date, int)

  def test_parse_bare_log(self):
    event = ParseEvents(retention, None, None, None).parse_line('15-02-11 20:37:48 area6_Leaf by chakapoko maker')
    self.assertIsInstance(event, EventBareLog)
    self.assertEqual(event.line, 'area6_Leaf by chakapoko maker')
    self.assertIsInstance(event.date, int)

  def test_parse_req_map(self):
    event = ParseEvents(retention, None, None, None).parse_line('16-03-11 11:34:59 [DDSSTINY] !map ctf_Rotten')
    self.assertIsInstance(event, EventRequestMap)
    self.assertEqual(event.map, 'ctf_Rotten')

  def test_parse_cmd_map_nick(self):
    event = ParseEvents(retention, None, None, None).parse_line('15-02-11 20:37:48 /map ctf_Guardian(78.50.103.50[IMP darDar])')
    self.assertIsInstance(event, EventNextMap)
    self.assertEqual(event.map, 'ctf_Guardian')

  def test_parse_cmd_restart(self):
    event = ParseEvents(retention, None, None, None).parse_line('15-02-11 20:37:48 /restart (78.50.103.50)')
    self.assertIsInstance(event, EventRestart)

  def test_parse_restart_notif(self):
    event = ParseEvents(retention, None, None, None).parse_line('15-02-11 20:37:48 Restarting...')
    self.assertIsInstance(event, EventRestart)

  def test_parse_invalid_map(self):
    event = ParseEvents(retention, None, None, None).parse_line('15-02-11 20:37:48 Map not found (ctf_Wretch)')
    self.assertIsInstance(event, EventInvalidMap)
    self.assertEqual(event.map, 'ctf_Wretch')

  def test_parse_score(self):
    event = ParseEvents(retention, None, None, None).parse_line('16-03-16 12:05:24 Gandalf scores for Alpha Team')
    self.assertIsInstance(event, EventScore)
    self.assertEqual(event.player, 'Gandalf')
    self.assertEqual(event.team, 'Alpha')
    self.assertIsInstance(event.date, int)

  def test_parse_kill_1(self):
    event = ParseEvents(retention, None, None, None).parse_line('16-03-26 02:56:20 (2) r|2 Der Exorzischt killed (1) r|3 Benedetta Zavatta with Grenade')
    self.assertIsInstance(event, Kill)
    self.assertEqual(event.killer, 'r|2 Der Exorzischt')
    self.assertEqual(event.victim, 'r|3 Benedetta Zavatta')
    self.assertEqual(event.weapon, 'Grenade')
    self.assertEqual(event.date, 1458986180)
    self.assertEqual(event.killer_team, 'bravo')
    self.assertEqual(event.victim_team, 'alpha')

  def test_parse_kill_2(self):
    event = ParseEvents(retention, None, None, None).parse_line('16-03-17 00:33:54 (1) \\\\F.O.S.T//Petterkowsk! killed (2) *>Spready<* with Grenade')
    self.assertIsInstance(event, Kill)
    self.assertEqual(event.killer, '\\\\F.O.S.T//Petterkowsk!')
    self.assertEqual(event.victim, '*>Spready<*')
    self.assertEqual(event.weapon, 'Grenade')
    self.assertEqual(event.killer_team, 'alpha')
    self.assertEqual(event.victim_team, 'bravo')

  def test_parse_kill_3(self):
    event = ParseEvents(retention, None, None, None).parse_line('16-03-01 03:04:21 (1) Vicious - MEXIKANO.Mx killed (2) r|2 Der Exorzischt with FN Minimi')
    self.assertIsInstance(event, Kill)
    self.assertEqual(event.killer, 'Vicious - MEXIKANO.Mx')
    self.assertEqual(event.victim, 'r|2 Der Exorzischt')
    self.assertEqual(event.weapon, 'FN Minimi')
    self.assertEqual(event.killer_team, 'alpha')
    self.assertEqual(event.victim_team, 'bravo')

  def test_parse_kill_4(self):
    event = ParseEvents(retention, None, None, None).parse_line('16-05-04 09:33:44 (0) jrgp killed (0) Zamyhrushka with Flame Bow')
    self.assertIsInstance(event, Kill)
    self.assertEqual(event.killer, 'jrgp')
    self.assertEqual(event.victim, 'Zamyhrushka')
    self.assertEqual(event.weapon, 'Bow')
    self.assertEqual(event.killer_team, 'none')
    self.assertEqual(event.victim_team, 'none')

  def test_parse_kill_5(self):
    event = ParseEvents(retention, None, None, None).parse_line('16-05-04 09:33:44 (0) jrgp killed (0) Zamyhrushka with Bow')
    self.assertIsInstance(event, Kill)
    self.assertEqual(event.killer, 'jrgp')
    self.assertEqual(event.victim, 'Zamyhrushka')
    self.assertEqual(event.weapon, 'Bow')
    self.assertEqual(event.killer_team, 'none')
    self.assertEqual(event.victim_team, 'none')

  def test_parse_shutdown(self):
    event = ParseEvents(retention, None, None, None).parse_line('18-09-19 04:10:47 Signal received, shutting down')
    self.assertIsInstance(event, EventShutdown)

    event = ParseEvents(retention, None, None, None).parse_line('18-09-19 04:10:47 Shutting down server...')
    self.assertIsInstance(event, EventShutdown)

  def test_get_time_out_of_filename(self):
    assert ParseEvents.get_time_out_of_filename('consolelog-18-03-16-04.txt') == ParseEvents.get_time_out_of_filename('consolelog-18-03-16-05.txt')
    assert ParseEvents.get_time_out_of_filename('consolelog-18-03-16-04.txt') == 1521183600
    with pytest.raises(ValueError):
      ParseEvents.get_time_out_of_filename('consolelsdfsdfog-18-03-16-04.txt')
