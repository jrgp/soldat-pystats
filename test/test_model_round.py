from piestats.models.round import Round

''' Verify that the Round model can pull data out of the redis hash correctly '''


def test_simple_fields():
  data = {
      'round_id': 10,
      'kills': 30,
      'map': 'ctf_Ash',
      'flags': 'yes',
      'scores:Alpha': 10,
      'scores:Bravo': 20,
  }

  r = Round(**data)

  assert r.id == 10
  assert r.kills == 30
  assert r.map == 'ctf_Ash'
  assert r.flagmatch is True


def test_winning_team():
  data = {
      'scores:Alpha': 10,
      'scores:Bravo': 20,
  }
  r = Round(**data)
  assert r.alpha_scores == 10
  assert r.bravo_scores == 20
  assert r.winning_team == 'bravo'

  data = {
      'scores:Alpha': 20,
      'scores:Bravo': 10,
  }
  r = Round(**data)
  assert r.alpha_scores == 20
  assert r.bravo_scores == 10
  assert r.winning_team == 'alpha'

  data = {
      'scores:Alpha': 10,
      'scores:Bravo': 10,
  }
  r = Round(**data)
  assert r.alpha_scores == 10
  assert r.bravo_scores == 10
  assert r.winning_team is None
  assert r.tie is True


def test_empty():
  data = {
      'started': 10,
      'finished': 20
  }

  r = Round(**data)
  assert r.empty is True

  data = {
      'scores:Alpha': 10,
  }

  r = Round(**data)
  assert r.empty is False


def test_timings():
  data = {
      'started': 10,
      'finished': 20
  }

  r = Round(**data)
  assert r.duration == 10

  data = {
      'started': 20,
      'finished': 10
  }

  r = Round(**data)
  assert r.duration == 0


def test_broken_data():
  data = {
      'scores:Alpha': 'foobar',
  }
  r = Round(**data)
  assert r.alpha_scores == 0


def test_players():
  assert Round().num_players == 0

  data = {
      'kills_player:1': 20,
      'kills_player:2': 10,
  }
  r = Round(**data)
  assert r.num_players == 2
