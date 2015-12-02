# TODO:

 - Bootstrap UI **done**
 - Gun pics for kill logs as well as weapon stats **done**
 - Record each players IPs and use Geo2Ip to look them up **done**
 - Include country flags **done**
 - Record each player's top enemies **done**
 - Make every playerlink have a country flag tied to it **done**
 - Work out how to record number of kills per each day and put a graph on front
   page. **done**
 - Make updater script *and* web ui script both take in an argument or default
   path to a config file that includes the soldat server dir, prefix for all
   redis keys, redis server connect info, and data retention. **done**
 - Data retention setting. Work by traversing kill log in reverse and decrementing
   stats each kill/event would have incremented if it is past the cutoff
   point. Also delete players with 0 kills/etc. **works**
 - Display each player's top enemies and victims **done**
 - Add support for multiple servers and a way to pick between them in the UI. **done**
 - Fix/refactor retention. Use a function for kill processing as well as kill
   reverting in the same exact code, to avoid duplication. **done**

 - Add ajax refresh parser to front page to get current server stats. **done**

 - add functionality to hit the server admin port and provide current
   stats from refreshx. **done**

 - Fix timezones. Store dates exclusively as pickled datetime objects, not stupid
   unix timestamp interpretations. Soldat appears to log kills in UTC.

 - Do away with logfile parsing and get kills by http requests coming from the
   Soldat servers scripts. This is blocked on a bug in scriptcore getting
   fixed.

 - Add realtime kill ingestion using beanstalkd or kafka. This will require a
   refactor to avoid a ton of code duplication. **fuck this**

 - Make this use Pinot/InfluxDB/Druid for its data source instead of redis, as
   it technically qualifies as an OLAP data tool. **kinda fuck this, as it's too
   much work for most people to install**
