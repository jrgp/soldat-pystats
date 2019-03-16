from piestats.update.decorateevents import decorate_events, decorate_event
from piestats.models.events import EventPlayerJoin, EventNextMap, EventScore, EventInvalidMap, EventRequestMap, EventBareLog, EventRestart, DecoratedEvent
from piestats.models.kill import Kill
from piestats.models.round import Round


class FakeRoundManager():
  def __init__(self, old_logfile_rounds=None):
    self.round_id = 0
    self.old_logfile_rounds = old_logfile_rounds
    self.finalized_rounds = set()

  def new_round(self, map, date, logfile):
    self.round_id += 1
    return self.round_id

  def finalize_round(self, round_id, date):
    self.finalized_rounds.add(round_id)

  def get_old_round_for_log(self, logfile):
    r = self.old_logfile_rounds.get(logfile)
    if r:
      self.round_id = r.id
      return r


def test_decorate_event():
  event = EventScore('Foobar', 'Alpha', 0),
  assert decorate_event(event, None, None) == DecoratedEvent(event, None, None)
  assert decorate_event(event, 'ctf_IceBeam', 10) == DecoratedEvent(event, 'ctf_IceBeam', 10)


def test_normal_map_change():
  events = [
      EventScore('Foobar', 'Alpha', 0),
      EventNextMap('ctf_IceBeam', 0),
      EventBareLog('IceBeam by Zakath, Suow, Poop', 0),
      EventScore('Foobar', 'Alpha', 0),
      EventNextMap('ctf_Ash', 0),
      EventScore('Foobar', 'Alpha', 0),
      EventBareLog('ASH', 0),
      EventScore('Foobar', 'Alpha', 0),
  ]

  map_titles = {
      'ctf_IceBeam': 'IceBeam by Zakath, Suow, Poop',
      'ctf_Ash': 'ASH'
  }

  assert list(decorate_events(events, map_titles)) == [
      DecoratedEvent(EventScore('Foobar', 'Alpha', 0), None, None),
      DecoratedEvent(EventScore('Foobar', 'Alpha', 0), 'ctf_IceBeam', None),
      DecoratedEvent(EventScore('Foobar', 'Alpha', 0), 'ctf_IceBeam', None),
      DecoratedEvent(EventScore('Foobar', 'Alpha', 0), 'ctf_Ash', None),
  ]


def test_player_map_change():
  events = [
      EventScore('Foobar', 'Alpha', 0),
      EventRequestMap('ctf_IceBeam', 0),
      EventBareLog('IceBeam by Zakath, Suow, Poop', 0),
      EventScore('Foobar', 'Alpha', 0),
      EventRequestMap('FooMap', 0),
      EventBareLog('FOOO', 0),
      EventScore('Foobar', 'Alpha', 0),
  ]

  map_titles = {
      'ctf_IceBeam': 'IceBeam by Zakath, Suow, Poop',
      'ctf_FooMap': 'FOOO'
  }

  assert list(decorate_events(events, map_titles)) == [
      DecoratedEvent(EventScore('Foobar', 'Alpha', 0), None, None),
      DecoratedEvent(EventScore('Foobar', 'Alpha', 0), 'ctf_IceBeam', None),
      DecoratedEvent(EventScore('Foobar', 'Alpha', 0), 'ctf_FooMap', None),
  ]


def test_restart_map_change():
  events = [
      EventRequestMap('ctf_IceBeam', 0),
      EventBareLog('IceBeam by Zakath, Suow, Poop', 0),
      EventScore('Foobar', 'Alpha', 0),
      EventRestart(0),
      EventBareLog('IceBeam by Zakath, Suow, Poop', 0),
      EventScore('Foobar', 'Alpha', 0),
  ]

  map_titles = {
      'ctf_IceBeam': 'IceBeam by Zakath, Suow, Poop'
  }

  assert list(decorate_events(events, map_titles)) == [
      DecoratedEvent(EventScore('Foobar', 'Alpha', 0), 'ctf_IceBeam', None),
      DecoratedEvent(EventScore('Foobar', 'Alpha', 0), 'ctf_IceBeam', None),
  ]


def test_kill():
  round_manager = FakeRoundManager()

  events = [
      EventNextMap('ctf_IceBeam', 0),
      EventBareLog('IceBeam by Zakath, Suow, Poop', 0),
      Kill('Blain', 'Zombie', 'MP5', 0)
  ]

  map_titles = {
      'ctf_IceBeam': 'IceBeam by Zakath, Suow, Poop'
  }

  decorated_events = list(decorate_events(events, map_titles=map_titles, round_manager=round_manager))
  assert len(decorated_events) == 1

  my_kill = decorated_events[0]

  assert my_kill.map == 'ctf_IceBeam'
  assert my_kill.round_id == 1


def test_round_1():
  round_manager = FakeRoundManager()

  events = [
      EventNextMap('ctf_IceBeam', 0),
      EventBareLog('IceBeam by Zakath, Suow, Poop', 0),
      EventScore('Foobar', 'Alpha', 0),

      EventNextMap('ctf_Ash', 0),
      EventBareLog('ASH', 0),
      EventScore('Foobar', 'Alpha', 0),
  ]

  map_titles = {
      'ctf_IceBeam': 'IceBeam by Zakath, Suow, Poop',
      'ctf_Ash': 'ASH'
  }

  assert list(decorate_events(events, map_titles=map_titles, round_manager=round_manager)) == [
      DecoratedEvent(EventScore('Foobar', 'Alpha', 0), 'ctf_IceBeam', 1),
      DecoratedEvent(EventScore('Foobar', 'Alpha', 0), 'ctf_Ash', 2),
  ]


def test_round_2():
  round_manager = FakeRoundManager()

  events = [
      EventRequestMap('ctf_IceBeam', 0),
      EventBareLog('IceBeam by Zakath, Suow, Poop', 0),
      EventScore('Foobar', 'Alpha', 0),
      EventRestart(0),
      EventBareLog('IceBeam by Zakath, Suow, Poop', 0),
      EventScore('Foobar', 'Alpha', 0),
  ]

  map_titles = {
      'ctf_IceBeam': 'IceBeam by Zakath, Suow, Poop',
      'ctf_Ash': 'ASH'
  }

  assert list(decorate_events(events, map_titles=map_titles, round_manager=round_manager)) == [
      DecoratedEvent(EventScore('Foobar', 'Alpha', 0), 'ctf_IceBeam', 1),
      DecoratedEvent(EventScore('Foobar', 'Alpha', 0), 'ctf_IceBeam', 2),
  ]

  assert round_manager.finalized_rounds == {1}


def test_round_recover():
  logfile = 'consolelog1.txt'

  round_manager = FakeRoundManager(old_logfile_rounds={
    logfile: Round(map='ctf_IceBeam', round_id=5)
  })

  events = [
      EventScore('Foobar', 'Alpha', 0),
      EventRestart(0),
      EventBareLog('IceBeam by Zakath, Suow, Poop', 0),
      EventScore('Foobar', 'Alpha', 0),
  ]

  map_titles = {
      'ctf_IceBeam': 'IceBeam by Zakath, Suow, Poop',
  }

  assert list(decorate_events(events, map_titles=map_titles, round_manager=round_manager, logfile=logfile)) == [
      DecoratedEvent(EventScore('Foobar', 'Alpha', 0), 'ctf_IceBeam', 5),
      DecoratedEvent(EventScore('Foobar', 'Alpha', 0), 'ctf_IceBeam', 6),
  ]

  assert round_manager.finalized_rounds == {5}


def test_ignore_players():
  events = [
      EventPlayerJoin('Joe', None, None, None),
      EventPlayerJoin('Major', None, None, None),
  ]

  ignore_players = ['Major']

  assert list(decorate_events(events, ignore_players=ignore_players)) == [
      DecoratedEvent(EventPlayerJoin('Joe', None, None, None), None, None)
  ]


def test_ignore_map():
  events = [
      EventRequestMap('ctf_IceBeam', 0),
      EventBareLog('IceBeam by Zakath, Suow, Poop', 0),
      EventScore('Foobar', 'Alpha', 0),

      EventRequestMap('ctf_Ash', 0),
      EventBareLog('ASH', 0),
      EventScore('Foobar', 'Alpha', 0),

      EventRequestMap('Bunker', 0),
      EventBareLog('BUNKER MAP', 0),
      EventScore('Foobar', 'Alpha', 0),
  ]

  ignore_maps = ['ctf_Ash']

  map_titles = {
      'ctf_IceBeam': 'IceBeam by Zakath, Suow, Poop',
      'ctf_Ash': 'ASH',
      'Bunker': 'BUNKER MAP',
  }

  assert list(decorate_events(events, ignore_maps=ignore_maps, map_titles=map_titles)) == [
      DecoratedEvent(EventScore('Foobar', 'Alpha', 0), 'ctf_IceBeam', None),
      DecoratedEvent(EventScore('Foobar', 'Alpha', 0), 'Bunker', None),
  ]
