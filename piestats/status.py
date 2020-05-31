import socket
import logging
from struct import unpack
import ipaddress
import geoip2.database
from collections import defaultdict
from piestats.compat import kill_bytes
import pkg_resources

logger = logging.getLogger(__name__)


class Status:

  def __init__(self, ip, port, password):
    self.ip = ip
    self.port = port
    self.password = password

    try:
      self.geoip = geoip2.database.open(pkg_resources.resource_filename('piestats.update', 'GeoLite2-Country.mmdb'))
    except Exception as e:
      logger.exception('Failed loading geoip db %s', e)
      self.geoip = None

  def parse_refresh(self, sock):
    ''' Use unpack/etc to parse the delphi struct '''

    # Base of what we'll give back
    info = {
        'players': defaultdict(dict),
        'ip': self.ip,
        'port': self.port,
        'country': False
    }

    # See http://wiki.soldat.pl/index.php/Refresh for docs on the binary response
    for i in range(0, 32):
      info['players'][i]['name'] = kill_bytes(unpack('25p', sock.recv(25))[0])

    for i in range(0, 32):
      info['players'][i]['team'] = unpack('B', sock.recv(1))[0]

    for i in range(0, 32):
      info['players'][i]['kills'] = unpack('H', sock.recv(2))[0]

    for i in range(0, 32):
      info['players'][i]['deaths'] = unpack('H', sock.recv(2))[0]

    for i in range(0, 32):
      info['players'][i]['ping'] = unpack('B', sock.recv(1))[0]

    for i in range(0, 32):
      info['players'][i]['id'] = unpack('B', sock.recv(1))[0]

    for i in range(0, 32):
      info['players'][i]['ip'] = '.'.join(map(str, unpack('4B', sock.recv(4))))

    info['score'] = {
        'alpha': unpack('H', sock.recv(2))[0],
        'bravo': unpack('H', sock.recv(2))[0],
        'charlie': unpack('H', sock.recv(2))[0],
        'delta': unpack('H', sock.recv(2))[0],
    }

    info['map'] = kill_bytes(unpack('17p', sock.recv(17))[0])
    info['timeLimit'] = unpack('i', sock.recv(4))[0]
    info['currentTime'] = unpack('i', sock.recv(4))[0]
    info['killLimit'] = unpack('H', sock.recv(2))[0]
    info['mode'] = unpack('B', sock.recv(1))[0]

    # We end up with a lot of empty player slots. Store keys to prune here
    empty_players = set()

    # Post processing of player results
    for key, player in info['players'].items():

      # Disregard this player if the name field is empty
      if player['name'] == '':
        empty_players.add(key)
        continue

      player['country'] = False
      player['bot'] = False

      # If player isn't a bot and IP is public try to get it to a country
      if player['ip'] == '0.0.0.0':
        player['bot'] = True
      elif not ipaddress.ip_address(player['ip']).is_private and self.geoip:
        try:
          match = self.geoip.country(player['ip']).country.iso_code
        except ValueError:
          pass
        else:
          player['country'] = match.lower()

    # Remove empty players
    for key in empty_players:
      del(info['players'][key])

    # Try doing an IP lookup on the server's IP, if it's public
    try:
      if not ipaddress.ip_address(player['ip']).is_private and self.geoip:
        match = self.geoip.country_code_by_addr(self.ip)
        if match:
          info['country'] = match.lower()

    # If we got a hostname instead of an IP we'll likely get this
    except ValueError:
      pass

    # Make the players object just an array
    info['players'] = list(info['players'].values())

    # Convenience
    info['minutesLeft'] = info['currentTime'] / 60 / 60
    info['botCount'] = len([x for x in info['players'] if x['bot']])

    return info

  def get_info(self):
    ''' Connect to server, send request for data and wait for it, then parse and return it '''

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(4.0)

    buf = ''
    info = None

    try:
      s.connect((self.ip, self.port))

      while True:
          data = s.recv(1)

          if not data:
              break

          buf = buf + data

          if buf.endswith('\n'):
              if buf == 'Soldat Admin Connection Established.\r\n':
                  logger.info('Connected to soldat server %s:%s', self.ip, self.port)
                  s.send('%s\n' % self.password)
              elif buf == 'Welcome, you are in command of the server now.\r\n':
                  logger.info('Authed')
                  s.send('REFRESH\n')
              elif buf == 'REFRESH\r\n':
                  logger.info('Refresh response inbound')
                  info = self.parse_refresh(s)
                  break

              buf = ''

    except socket.error as e:
      logger.exception('Socket problem with soldat server %s:%s: %s', self.ip, self.port, e)
      return None

    finally:
      s.close()

    return info
