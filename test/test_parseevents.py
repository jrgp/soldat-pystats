import unittest
from piestats.update.parseevents import ParseEvents
from piestats.models.events import EventPlayerJoin, EventNextMap, EventScore


class TestParseEvents(unittest.TestCase):

  def test_parse_player_join(self):
    event = ParseEvents(None).parse_events('15-01-30 23:34:09 rage rage foo rage joining game (84.120.15.45:23073) HWID:4DD3F08B8AA').next()
    self.assertIsInstance(event, EventPlayerJoin)
    self.assertEqual(event.player, 'rage rage foo rage')
    self.assertEqual(event.ip, '84.120.15.45')

  def test_parse_next_map(self):
    event = ParseEvents(None).parse_events('15-02-11 20:37:48 Next map: Blox').next()
    self.assertIsInstance(event, EventNextMap)
    self.assertEqual(event.map, 'Blox')

  def test_parse_score(self):
    event = ParseEvents(None).parse_events('16-03-16 12:05:24 Gandalf scores for Alpha Team').next()
    self.assertIsInstance(event, EventScore)
    self.assertEqual(event.player, 'Gandalf')
    self.assertEqual(event.team, 'Alpha')


if __name__ == '__main__':
  unittest.main()
