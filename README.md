# soldat-pystats

Statistics script which displays kill and player/country stats for multiple
[Soldat](http://soldat.pl/) game servers. Powered by Python + [Redis](http://redis.io/) + [Falcon](https://falconframework.org/) and styled with [Bootswatch](http://bootswatch.com/).

# Screenshots

 - [Home Page](http://jrgp.us/screenshots/soldat-pystats1.png)
 - [Players list](http://jrgp.us/screenshots/soldat-pystats2.png)
 - [Player profile](http://jrgp.us/screenshots/soldat-pystats3.png)
 - [Map Profile with polygon view](http://jrgp.us/screenshots/soldat-pystats_map1.png)

# Features

 - Get logs from either local files, or ssh+sftp, or FTP on a remote game host
 - ip2country for all players. Country stats + flags next to each player
 - Automatic intelligent merging of player names sharing HWIDs
 - Supports multiple Soldat servers
 - Configurable data retention. Don't show kill stats more than X days old.
 - Ability to connect to Soldat server's admin port and provide current status
 - Player search
 - Pretty graphs
 - Display wireframe image of map polygons
 - Clean comfortable layout provided by Bootswatch
 - Uses Redis key value database instead of SQL so pages are fast even with
   millions of recorded kills.
 - HTML or JSON output for data. To get JSON, `?json=yes` to any URL, or request json using the `Accept` header

# Requirements

- Python 2.7, with virtualenv/pip tools
- Redis DB installed/running
- Tested with soldat server version 2.8.1. You must have `EchoKills=1` set in `server.ini`

# Instructions

Install GeoIP lib and update the database:

    sudo apt-get install libgeoip-dev libgeoip1
    curl -s http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz | gzip -d > piestats/update/GeoIP.dat

First, have an install of Redis database runnning. The following will do.

    sudo apt-get install redis-server

### Dev guide/Quickstart

Install python virtualenv tool as well as build dependencies

    sudo apt-get install python-virtualenv python-dev

Create & activate venv (run this before next commands):

    virtualenv env
    source env/bin/activate

To install to your venv but point to your code so you can edit and dev and run:

    python setup.py develop

Copy `config.yml.samp` to `config.yml` after editing it to fit your setup

Run update script. Probably add this to cron.

    piestats update -c config.yml

Quickly start website. (Bind to all NICs on port 5000)

    piestats web -c config.yml

# Gunicorn Example

Use a command like the following to run pystats under gunicorn, listening on port 5000, for production instead of dev.

    gunicorn 'piestats.web:init_app()' -b 0:5000 --max-requests 1000 -w 4 -k gevent --access-logfile - -e PYSTATS_CONF=config.yml

If huge QPS is needed, using uwsgi instead of gunicorn would be better.

# Contact
 - Joe Gillotti - <joe@u13.net>
 - [GitHub](https://github.com/jrgp/soldat-pystats)
 - License: MIT
