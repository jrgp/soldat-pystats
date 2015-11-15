import socket
import re
import logging
from struct import unpack
from collections import namedtuple, defaultdict
from IPy import IP
from geoip import geolite2

Player = namedtuple('Player', ['name', 'team', 'kills', 'deaths', 'ping', 'id', 'ip'])


class Status:
  ''' This refresh-parsing implementation based on my 2013 code here: http://wiki.soldat.pl/index.php/Refresh#Python '''

  def __init__(self, ip, port, password):
    self.ip = ip
    self.port = port
    self.password = password

  def parse_refresh(self, sock):
    ''' Use unpack and friends to parse the binary refresh blob '''

    logging.info('parsing data')
 
    players = defaultdict(dict)
    info = {}
 
    for i in range(0, 32):
        nameLength = unpack('B', sock.recv(1))[0]
        players[i]['name'] = sock.recv(nameLength)
        sock.recv(24 - nameLength)
 
    for i in range(0, 32):
        players[i]['team'] = unpack('B', sock.recv(1))[0]
 
    for i in range(0, 32):
        players[i]['kills'] = unpack('H', sock.recv(2))[0]
 
    for i in range(0, 32):
        players[i]['deaths'] = unpack('H', sock.recv(2))[0]
 
    for i in range(0, 32):
        players[i]['ping'] = unpack('B', sock.recv(1))[0]
 
    for i in range(0, 32):
        players[i]['id'] = unpack('B', sock.recv(1))[0]
 
    for i in range(0, 32):
        players[i]['ip'] = '.'.join([str(v) for v in unpack('BBBB', sock.recv(4))])
 
    info['score'] = {
        'alpha': unpack('H', sock.recv(2))[0],
        'bravo': unpack('H', sock.recv(2))[0],
        'charlie': unpack('H', sock.recv(2))[0],
        'delta': unpack('H', sock.recv(2))[0],
    }
 
    mapLength = unpack('B', sock.recv(1))[0]
    info['map'] = sock.recv(mapLength)
    sock.recv(16 - mapLength)
 
    info['timeLimit'] = unpack('i', sock.recv(4))[0] / 60
    info['currentTime'] = unpack('i', sock.recv(4))[0] / 60
    info['killLimit'] = unpack('H', sock.recv(2))[0]
    info['mode'] = unpack('B', sock.recv(1))[0]
 
    logging.info('info: {0}'.format(info))

    info['players'] = []

    for player in players.itervalues():
      if player['name'] == '':
        continue

      country = False
      if IP(player['ip']).iptype() == 'PUBLIC':
        match = geolite2.lookup(player['ip'])
        if match:
          country = match.country.lower()

      info['players'].append(dict(
        name=player['name'],
        kills=player['kills'],
        deaths=player['deaths'],
        team=player['team'],
        country=country
      ))

    info['country'] = 'us'
    info['ip'] = self.ip
    info['port'] = self.port

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
        except Exception as e:
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
                logging.info('refresh packet inbound')
                info = self.parse_refresh(s)
                break
            # else:
            #    print buf
     
            buf = ''
     
    s.close()

    return info
