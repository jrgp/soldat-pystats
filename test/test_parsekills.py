import unittest
from piestats.models.kill import Kill
from piestats.update.parsekills import ParseKills
from mock import MagicMock


class TestParseKills(unittest.TestCase):

  def test_parse_kill(self):
    text = '''
--- 16-03-26 02:56:20
Gandalf
Ops! - magnum
M79
'''

    retention_mock = MagicMock()
    retention_mock.configure_mock(**{'too_old.return_value': False})

    item = ParseKills(retention_mock, None).parse_kills(text).next()

    self.assertIsInstance(item, Kill)
    self.assertEqual(item.killer, 'Gandalf')
    self.assertEqual(item.victim, 'Ops! - magnum')
    self.assertEqual(item.weapon, 'M79')
    self.assertEqual(item.timestamp, 1458986180)


if __name__ == '__main__':
  unittest.main()
