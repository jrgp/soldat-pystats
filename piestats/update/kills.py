from datetime import datetime
import pickle


def apply_kill(r, keys, kill, incr=1):

  # Add kill to global kill log
  if incr == 1:
    r.lpush(keys.kill_log, pickle.dumps(kill))

  # Stuff that only makes sense for non suicides
  if not kill.suicide:
    r.zincrby(keys.top_players, kill.killer, incr)
    r.hincrby(keys.player_hash(kill.killer), 'kills', incr)

  # Increment number of deaths for victim
  r.hincrby(keys.player_hash(kill.victim), 'deaths', incr)

  # Update first/last time we saw player
  if incr == 1:
    r.hsetnx(keys.player_hash(kill.killer), 'firstseen', kill.timestamp)
    r.hset(keys.player_hash(kill.killer), 'lastseen', kill.timestamp)

  # Update first/last time we saw victim, if they're not the same..
  if incr == 1 and not kill.suicide:
    r.hsetnx(keys.player_hash(kill.victim), 'firstseen', kill.timestamp)
    r.hset(keys.player_hash(kill.victim), 'lastseen', kill.timestamp)

  # Update weapon stats..
  if not kill.suicide:
    r.zincrby(keys.top_weapons, kill.weapon)
    r.hincrby(keys.player_hash(kill.killer), 'kills:' + kill.weapon, incr)
    r.hincrby(keys.player_hash(kill.victim), 'deaths:' + kill.weapon, incr)

  # If we're not a suicide, update top enemy kills for player..
  if not kill.suicide:
    # Top people the killer has killed
    r.zincrby(keys.player_top_enemies(kill.killer), kill.victim, incr)

    # Top people the victim has died by
    r.zincrby(keys.player_top_victims(kill.victim), kill.killer, incr)

  # If we're not a sucide, add this legit kill to the number of kills for this
  # day
  if not kill.suicide:
    text_today = str(datetime.utcfromtimestamp(kill.timestamp).date())
    r.incr(keys.kills_per_day(text_today), incr)
