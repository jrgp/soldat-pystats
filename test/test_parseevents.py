import pytest
from piestats.update.parseevents import ParseEvents
from piestats.models.events import EventPlayerJoin, EventNextMap, EventScore, EventInvalidMap, EventRequestMap, EventBareLog, EventShutdown, EventRestart
from piestats.models.kill import Kill


def test_parse_player_join():
  event = ParseEvents(None, None, None, None).parse_line('15-01-30 23:34:09 rage rage foo rage joining game (84.120.15.45:23073) HWID:4DD3F08B8AA')
  assert isinstance(event, EventPlayerJoin)
  assert event.player == 'rage rage foo rage'
  assert event.ip == '84.120.15.45'
  assert event.hwid == '4DD3F08B8AA'
  assert isinstance(event.date, int)


def test_parse_next_map():
  event = ParseEvents(None, None, None, None).parse_line('15-02-11 20:37:48 Next map: Blox')
  assert isinstance(event, EventNextMap)
  assert event.map == 'Blox'
  assert isinstance(event.date, int)


def test_parse_cmd_map():
  event = ParseEvents(None, None, None, None).parse_line('15-02-11 20:37:48 /map ctf_Wretch (198.136.48.50)')
  assert isinstance(event, EventNextMap)
  assert event.map == 'ctf_Wretch'
  assert isinstance(event.date, int)


def test_parse_bare_log():
  event = ParseEvents(None, None, None, None).parse_line('15-02-11 20:37:48 area6_Leaf by chakapoko maker')
  assert isinstance(event, EventBareLog)
  assert event.line == 'area6_Leaf by chakapoko maker'
  assert isinstance(event.date, int)


def test_parse_req_map():
  event = ParseEvents(None, None, None, None).parse_line('16-03-11 11:34:59 [DDSSTINY] !map ctf_Rotten')
  assert isinstance(event, EventRequestMap)
  assert event.map == 'ctf_Rotten'


def test_parse_cmd_map_nick():
  event = ParseEvents(None, None, None, None).parse_line('15-02-11 20:37:48 /map ctf_Guardian(78.50.103.50[IMP darDar])')
  assert isinstance(event, EventNextMap)
  assert event.map == 'ctf_Guardian'


def test_parse_cmd_restart():
  event = ParseEvents(None, None, None, None).parse_line('15-02-11 20:37:48 /restart (78.50.103.50)')
  assert isinstance(event, EventRestart)


def test_parse_restart_notif():
  event = ParseEvents(None, None, None, None).parse_line('15-02-11 20:37:48 Restarting...')
  assert isinstance(event, EventRestart)


def test_parse_invalid_map():
  event = ParseEvents(None, None, None, None).parse_line('15-02-11 20:37:48 Map not found (ctf_Wretch)')
  assert isinstance(event, EventInvalidMap)
  assert event.map == 'ctf_Wretch'


def test_parse_score():
  event = ParseEvents(None, None, None, None).parse_line('16-03-16 12:05:24 Gandalf scores for Alpha Team')
  assert isinstance(event, EventScore)
  assert event.player == 'Gandalf'
  assert event.team == 'Alpha'
  assert isinstance(event.date, int)


def test_parse_kill_1():
  event = ParseEvents(None, None, None, None).parse_line('16-03-26 02:56:20 (2) r|2 Der Exorzischt killed (1) r|3 Benedetta Zavatta with Grenade')
  assert isinstance(event, Kill)
  assert event.killer == 'r|2 Der Exorzischt'
  assert event.victim == 'r|3 Benedetta Zavatta'
  assert event.weapon == 'Grenade'
  assert event.date == 1458960980
  assert event.killer_team == 'bravo'
  assert event.victim_team == 'alpha'


def test_parse_kill_2():
  event = ParseEvents(None, None, None, None).parse_line('16-03-17 00:33:54 (1) \\\\F.O.S.T//Petterkowsk! killed (2) *>Spready<* with Grenade')
  assert isinstance(event, Kill)
  assert event.killer == '\\\\F.O.S.T//Petterkowsk!'
  assert event.victim == '*>Spready<*'
  assert event.weapon == 'Grenade'
  assert event.killer_team == 'alpha'
  assert event.victim_team == 'bravo'


def test_parse_kill_3():
  event = ParseEvents(None, None, None, None).parse_line('16-03-01 03:04:21 (1) Vicious - MEXIKANO.Mx killed (2) r|2 Der Exorzischt with FN Minimi')
  assert isinstance(event, Kill)
  assert event.killer == 'Vicious - MEXIKANO.Mx'
  assert event.victim == 'r|2 Der Exorzischt'
  assert event.weapon == 'FN Minimi'
  assert event.killer_team == 'alpha'
  assert event.victim_team == 'bravo'


def test_parse_kill_4():
  event = ParseEvents(None, None, None, None).parse_line('16-05-04 09:33:44 (0) jrgp killed (0) Zamyhrushka with Flame Bow')
  assert isinstance(event, Kill)
  assert event.killer == 'jrgp'
  assert event.victim == 'Zamyhrushka'
  assert event.weapon == 'Bow'
  assert event.killer_team == 'none'
  assert event.victim_team == 'none'


def test_parse_kill_5():
  event = ParseEvents(None, None, None, None).parse_line('16-05-04 09:33:44 (0) jrgp killed (0) Zamyhrushka with Bow')
  assert isinstance(event, Kill)
  assert event.killer == 'jrgp'
  assert event.victim == 'Zamyhrushka'
  assert event.weapon == 'Bow'
  assert event.killer_team == 'none'
  assert event.victim_team == 'none'


def test_parse_shutdown():
  event = ParseEvents(None, None, None, None).parse_line('18-09-19 04:10:47 Signal received, shutting down')
  assert isinstance(event, EventShutdown)

  event = ParseEvents(None, None, None, None).parse_line('18-09-19 04:10:47 Shutting down server...')
  assert isinstance(event, EventShutdown)


def test_get_time_out_of_filename():
  assert ParseEvents.get_time_out_of_filename('consolelog-18-03-16-04.txt') == ParseEvents.get_time_out_of_filename('consolelog-18-03-16-05.txt')
  assert ParseEvents.get_time_out_of_filename('consolelog-18-03-16-04.txt') == 1521183600
  with pytest.raises(ValueError):
    ParseEvents.get_time_out_of_filename('consolelsdfsdfog-18-03-16-04.txt')
