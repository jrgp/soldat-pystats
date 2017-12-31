import socket
import re
import logging
from struct import unpack
from IPy import IP
import GeoIP
from collections import defaultdict
import pkg_resources


class Status:

  def __init__(self, ip, port, password):
    self.ip = ip
    self.port = port
    self.password = password

    try:
      self.geoip = GeoIP.open(pkg_resources.resource_filename('piestats.update', 'GeoIP.dat'), GeoIP.GEOIP_MMAP_CACHE)
    except Exception as e:
      print 'Failed loading geoip db %s' % e
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
    for i in xrange(0, 32):
      info['players'][i]['name'] = unpack('25p', sock.recv(25))[0]

    for i in xrange(0, 32):
      info['players'][i]['team'] = unpack('B', sock.recv(1))[0]

    for i in xrange(0, 32):
      info['players'][i]['kills'] = unpack('H', sock.recv(2))[0]

    for i in xrange(0, 32):
      info['players'][i]['deaths'] = unpack('H', sock.recv(2))[0]

    for i in xrange(0, 32):
      info['players'][i]['ping'] = unpack('B', sock.recv(1))[0]

    for i in xrange(0, 32):
      info['players'][i]['id'] = unpack('B', sock.recv(1))[0]

    for i in xrange(0, 32):
      info['players'][i]['ip'] = '.'.join(map(str, unpack('4B', sock.recv(4))))

    info['score'] = {
        'alpha': unpack('H', sock.recv(2))[0],
        'bravo': unpack('H', sock.recv(2))[0],
        'charlie': unpack('H', sock.recv(2))[0],
        'delta': unpack('H', sock.recv(2))[0],
    }

    info['map'] = unpack('17p', sock.recv(17))[0]
    info['timeLimit'] = unpack('i', sock.recv(4))[0]
    info['currentTime'] = unpack('i', sock.recv(4))[0]
    info['killLimit'] = unpack('H', sock.recv(2))[0]
    info['mode'] = unpack('B', sock.recv(1))[0]

    # We end up with a lot of empty player slots. Store keys to prune here
    empty_players = set()

    # Post processing of player results
    for key, player in info['players'].iteritems():

      # Disregard this player if the name field is empty
      if player['name'] == '':
        empty_players.add(key)
        continue

      player['country'] = False
      player['bot'] = False

      # If player isn't a bot and IP is public try to get it to a country
      if player['ip'] == '0.0.0.0':
        player['bot'] = True
      elif IP(player['ip']).iptype() == 'PUBLIC' and self.geoip:
        match = self.geoip.country_code_by_addr(player['ip'])
        if match:
          player['country'] = match.lower()

    # Remove empty players
    for key in empty_players:
      del(info['players'][key])

    # Try doing an IP lookup on the server's IP, if it's public
    try:
      if IP(self.ip).iptype() == 'PUBLIC' and self.geoip:
        match = self.geoip.country_code_by_addr(self.ip)
        if match:
          info['country'] = match.lower()

    # If we got a hostname instead of an IP we'll likely get this
    except ValueError:
      pass

    # Make the players object just an array
    info['players'] = info['players'].values()

    # Convenience
    info['minutesLeft'] = info['currentTime'] / 60 / 60
    info['botCount'] = len(filter(lambda x: x['bot'], info['players']))

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

            buf = ''

    s.close()

    return info
