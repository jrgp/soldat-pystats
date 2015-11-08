Dev instructions:

To install to your venv but point to your code so you can edit and dev:
  python setup.py develop

To actually install:
  python setup.py install

Run update script:
  runupdate

Start website:
  runsite

(Above will someday use config files to change settings)


TODO:

 - Bootstrap UI **done**
 - Gun pics for kill logs as well as weapon stats **done**
 - Record each players IPs and use Geo2Ip to look them up **done**
 - Include country flags **done**
 - Record each player's top enemies **done**
 - Make every playerlink have a country flag tied to it **done**
 - Work out how to record number of kills per each day and put a graph on front
   page. **done**

 - Display each player's top enemies and victims
 
 - Make updater script *and* web ui script both take in an argument or default
   path to a config file that includes the soldat server dir, prefix for all
   redis keys, redis server connect info, and data retention.

 - Data retention setting. Work by traversing kill log in reverse and decrementing
   stats each kill/event would have incremented if it is past the cutoff
   point. Also delete players with 0 kills/etc.
