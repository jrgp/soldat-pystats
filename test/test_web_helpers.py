from piestats.web.helpers import remove_redundant_player_names
import unittest


class TestWebHelpers(unittest.TestCase):
    def test_remove_redundant_player_names(self):
        assert(remove_redundant_player_names(['foobar', 'foofoo'])) == ['foobar', 'foofoo']
        assert(remove_redundant_player_names(['foobar', 'Major'])) == ['foobar', 'Major']
        assert(remove_redundant_player_names(['Major', 'Major(1)'])) == ['Major']
        assert(remove_redundant_player_names(['Major', 'Major(1)', 'Major(2)'])) == ['Major']
        assert(remove_redundant_player_names(['Major', 'Major(1)', 'Major(2)', 'Major(2)'])) == ['Major']
        assert(remove_redundant_player_names(['Major', 'Major(1)', 'Major(2)', 'Major(3)', 'John(5)'])) == ['Major', 'John(5)']


if __name__ == '__main__':
  unittest.main()
