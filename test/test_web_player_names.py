from piestats.web.player_names import remove_redundant_player_names


def test_remove_redundant_player_names():
  assert remove_redundant_player_names(['foobar', 'foofoo']) == ['foobar', 'foofoo']
  assert remove_redundant_player_names(['foobar', 'Major']) == ['foobar', 'Major']
  assert remove_redundant_player_names(['Major', 'Major(1)']) == ['Major']
  assert remove_redundant_player_names(['Major', 'Major(1)', 'Major(2)']) == ['Major']
  assert remove_redundant_player_names(['Major', 'Major(1)', 'Major(2)', 'Major(2)']) == ['Major']
  assert remove_redundant_player_names(['Major', 'Major(1)', 'Major(2)', 'Major(3)', 'John(5)']) == ['Major', 'John(5)']
