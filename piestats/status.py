import socket
import ctypes
import re
import logging
from IPy import IP
from geoip import geolite2


class _refresh_player_name(ctypes.Structure):
  _fields_ = [('length', ctypes.c_ubyte), ('text', ctypes.c_char * 24)]


class _refresh_player_ip(ctypes.Structure):
  _fields_ = [('ip', ctypes.c_ubyte * 4)]


class _refresh_map_name(ctypes.Structure):
  _fields_ = [('length', ctypes.c_ubyte), ('text', ctypes.c_char * 16)]


class RefreshStruct(ctypes.Structure):
  _fields_ = [
      ('player_names', _refresh_player_name * 32),
      ('player_teams', ctypes.c_ubyte * 32),
      ('player_kills', ctypes.c_ushort * 32),
      ('player_deaths', ctypes.c_ushort * 32),
      ('player_ping', ctypes.c_ubyte * 32),
      ('player_id', ctypes.c_ubyte * 32),
      ('player_ip', _refresh_player_ip * 32),
      ('score_alpha', ctypes.c_ushort),
      ('score_bravo', ctypes.c_ushort),
      ('score_charlie', ctypes.c_ushort),
      ('score_delta', ctypes.c_ushort),
      ('map_name', _refresh_map_name),
      ('time_limit', ctypes.c_int),
      ('current_time', ctypes.c_int),
      ('kill_limit', ctypes.c_ushort),
      ('mode', ctypes.c_ubyte),
  ]


class Status:

  def __init__(self, ip, port, password):
    self.ip = ip
    self.port = port
    self.password = password

  def parse_refresh(self, sock):
    ''' Use ctypes to parse the delphi struct '''

    response = RefreshStruct()
    sock.recv_into(response)

    info = {
        'score': {
            'alpha': response.score_alpha,
            'bravo': response.score_bravo,
            'charlie': response.score_charlie,
            'delta': response.score_delta,
        },
        'map': response.map_name.text[:response.map_name.length],
        'timeLimit': response.time_limit / 60,
        'currentTime': response.current_time / 60,
        'killLimit': response.kill_limit,
        'mode': response.mode,
        'players': [],
        'ip': self.ip,
        'port': self.port,
        'country': False
    }

    if IP(self.ip).iptype() == 'PUBLIC':
      match = geolite2.lookup(self.ip)
      if match:
        info['country'] = match.country.lower()

    for i, name in enumerate(response.player_names):
      player_name = name.text[:name.length]
      if player_name == '':
        continue

      ip = '.'.join(map(str, response.player_ip[i].ip))

      country = False
      if IP(ip).iptype() == 'PUBLIC':
        match = geolite2.lookup(ip)
        if match:
          country = match.country.lower()

      info['players'].append(dict(  # noqa
        name=player_name,
        kills=response.player_kills[i],
        deaths=response.player_deaths[i],
        team=response.player_teams[i],
        ping=response.player_ping[i],
        country=country
      ))

    return info

  def get_info(self):
    ''' Connect to server, send request for data and wait for it, then parse and return it '''

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((self.ip, self.port))

    buf = ''

    info = None

    while True:
        try:
            data = s.recv(1)
        except Exception:
            break

        if not data:
            break

        buf = buf + data

        if re.search('\r?\n$', buf):
            if buf == 'Soldat Admin Connection Established.\r\n':
                logging.info('connected')
                s.send('%s\n' % self.password)
            elif buf == 'Welcome, you are in command of the server now.\r\n':
                logging.info('authed')
                s.send('REFRESH\n')
            elif buf == 'REFRESH\r\n':
                logging.info('refresh response inbound')
                info = self.parse_refresh(s)
                break
            # else:
            #    print buf

            buf = ''

    s.close()

    return info
