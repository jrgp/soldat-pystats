
Dev instructions:

To install to your venv but point to your code so you can edit and dev:
  python setup.py develop

To actually install:
  python setup.py install

Run update script:
  update -d path/to/soldatserver/directory -r redisServer


TODO:

 - Bootstrap UI
 - Gun pics for kill logs as well as weapon stats
 - Record each player's top enemies
 - Record each player's IPs and use Geo2Ip to look them up
 - Include country flags
 - Make updater script take in path to soldat server as an arg as well as 
   redis confs. Use either args for this *or* an optional cfg parse. For
   args, use click
 - Make every playerlink have a country flag tied to it
 
 - Pages:
    - Latest kills / leader boards
    - 
