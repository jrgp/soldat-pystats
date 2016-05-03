import unittest
from piestats.update.parseevents import ParseEvents
from piestats.models.events import EventPlayerJoin, EventNextMap, EventScore
from piestats.models.kill import Kill
from mock import MagicMock

retention = MagicMock()
retention.configure_mock(**{'too_old.return_value': False})


class TestParseEvents(unittest.TestCase):

  def test_parse_player_join(self):
    event = ParseEvents(retention, None).parse_events('15-01-30 23:34:09 rage rage foo rage joining game (84.120.15.45:23073) HWID:4DD3F08B8AA').next()
    self.assertIsInstance(event, EventPlayerJoin)
    self.assertEqual(event.player, 'rage rage foo rage')
    self.assertEqual(event.ip, '84.120.15.45')

  def test_parse_next_map(self):
    event = ParseEvents(retention, None).parse_events('15-02-11 20:37:48 Next map: Blox').next()
    self.assertIsInstance(event, EventNextMap)
    self.assertEqual(event.map, 'Blox')

  def test_parse_score(self):
    event = ParseEvents(retention, None).parse_events('16-03-16 12:05:24 Gandalf scores for Alpha Team').next()
    self.assertIsInstance(event, EventScore)
    self.assertEqual(event.player, 'Gandalf')
    self.assertEqual(event.team, 'Alpha')

  def test_parse_kill_1(self):
    event = ParseEvents(retention, None).parse_events('16-03-26 02:56:20 (2) r|2 Der Exorzischt killed (1) r|3 Benedetta Zavatta with Grenade').next()
    self.assertIsInstance(event, Kill)
    self.assertEqual(event.killer, 'r|2 Der Exorzischt')
    self.assertEqual(event.victim, 'r|3 Benedetta Zavatta')
    self.assertEqual(event.weapon, 'Grenade')
    self.assertEqual(event.timestamp, 1458986180)

  def test_parse_kill_2(self):
    event = ParseEvents(retention, None).parse_events('16-03-17 00:33:54 (1) \\\\F.O.S.T//Petterkowsk! killed (2) *>Spready<* with Grenade').next()
    self.assertIsInstance(event, Kill)
    self.assertEqual(event.killer, '\\\\F.O.S.T//Petterkowsk!')
    self.assertEqual(event.victim, '*>Spready<*')
    self.assertEqual(event.weapon, 'Grenade')

  def test_parse_kill_3(self):
    event = ParseEvents(retention, None).parse_events('16-03-01 03:04:21 (1) Vicious - MEXIKANO.Mx killed (2) r|2 Der Exorzischt with FN Minimi').next()
    self.assertIsInstance(event, Kill)
    self.assertEqual(event.killer, 'Vicious - MEXIKANO.Mx')
    self.assertEqual(event.victim, 'r|2 Der Exorzischt')
    self.assertEqual(event.weapon, 'FN Minimi')


if __name__ == '__main__':
  unittest.main()
