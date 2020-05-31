from time import time
from collections import deque
from piestats.compat import kill_bytes


class BoundedCache:
    ''' Simplistic bounded LRU cache '''
    def __init__(self, maxsize=100):
        self.maxsize = maxsize
        self.keys = deque()
        self.dict = {}

    def get(self, key):
        cached = self.dict.get(key)
        if cached:
            self.keys.remove(key)
            self.keys.appendleft(key)
            return cached

    def set(self, key, value):
        if key in self.dict:
            self.dict[key] = value
            self.keys.remove(key)
            self.keys.appendleft(key)
            return

        if len(self.dict) > self.maxsize:
            evict = self.keys.pop()
            self.dict.pop(evict)

        self.dict[key] = value
        self.keys.appendleft(key)


class Hwid:
    ''' Attempt to dedupe player names based on HWID. Optimistic with caveats. '''
    def __init__(self, r, keys, verbose=False):
        self.r = r
        self.keys = keys
        self.player_name_cache = BoundedCache(1000)
        self.verbose = verbose

    def get_player_id_from_name(self, name):
        ''' get what player id this name currently maps to. if there is none, instantiate one '''
        # Refer to our local cache
        cached = self.player_name_cache.get(name)
        if cached:
            return cached

        existing_name_id = kill_bytes(self.r.hget(self.keys.name_to_id, name))

        # Case where we have track of player joining
        if existing_name_id is not None:
            player_id = int(existing_name_id)

        # Case where we don't. Bot? Start it off.
        else:
            player_id = int(self.r.incr(self.keys.last_player_id))
            self.r.hset(self.keys.name_to_id, name, player_id)
            self.r.zadd(self.keys.player_id_to_names(player_id), {name: time()})

        self.player_name_cache.set(name, player_id)

        return player_id

    def register_hwid(self, name, hwid, date):
        '''
          crux of hwid dedupe functionality.
          called based on the "player join" console log lines. instantiate a player ID for this name or tie it to an existing name
        '''
        # Try to formulate proper mapping of hwid to id
        existing_hwid_id = kill_bytes(self.r.hget(self.keys.hwid_to_id, hwid))
        existing_name_id = kill_bytes(self.r.hget(self.keys.name_to_id, name))

        if existing_hwid_id is not None:
            existing_hwid_id = int(existing_hwid_id)

        if existing_name_id is not None:
            existing_name_id = int(existing_name_id)

        # No ID for this combo set yet? Map it
        if existing_hwid_id is None and existing_name_id is None:
            player_id = int(self.r.incr(self.keys.last_player_id))

            self.r.hset(self.keys.hwid_to_id, hwid, player_id)
            self.r.hset(self.keys.name_to_id, name, player_id)

        # HWID has an ID but name doesn't? Player used a different name. Store same player ID.
        elif existing_hwid_id is not None and existing_name_id is None:
            player_id = existing_hwid_id
            self.r.hset(self.keys.name_to_id, name, player_id)

        # New ID but same name? Meh. Fuck it. Bind them together.
        elif existing_hwid_id is None and existing_name_id is not None:
            player_id = existing_name_id
            self.r.hset(self.keys.hwid_to_id, hwid, player_id)

        # We have both saved already. Sanity check?
        elif existing_hwid_id is not None and existing_name_id is not None:
            # Garbage fire of many-to-many mapping of HWID to playername
            if existing_hwid_id != existing_name_id:
                player_id = existing_hwid_id
                if self.verbose:
                    print('\nMismatch of IDs. HWID "%s" (%s) does not match Name "%s" (id %s). Defaulting to %s' % (
                          hwid, existing_hwid_id, name, existing_name_id, player_id))
                self.r.hset(self.keys.hwid_to_id, hwid, player_id)
                self.r.hset(self.keys.name_to_id, name, player_id)

            # They match. All good. No confusion or bullshit. Repeated player with same name and same HWID.
            else:
                player_id = existing_hwid_id

        # Keep track of latest name per this ID
        self.r.zadd(self.keys.player_id_to_names(player_id), {name: date})

        # Also lastseen/firstseen accordingly for this player ID
        self.r.hsetnx(self.keys.player_hash(player_id), 'firstseen', date)
        old_last_seen = int(kill_bytes(self.r.hget(self.keys.player_hash(player_id), 'lastseen')) or 0)
        if date > old_last_seen:
          self.r.hset(self.keys.player_hash(player_id), 'lastseen', date)

        return player_id
