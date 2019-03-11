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

### Quickstart

Install python virtualenv tool as well as build dependencies

    sudo apt-get install python-virtualenv python-dev libyaml-dev

Download latest version of pystats

    git clone https://github.com/jrgp/soldat-pystats.git
    cd soldat-pystats

Create & activate venv (run this before next commands):

    virtualenv env
    source env/bin/activate

To install to your venv but point to your code so you can edit and dev and run:

    python setup.py develop

Copy `config.yml.samp` to `config.yml` after editing it to fit your setup

Quickly start website. (Bind to all NICs on port 5000). You can change the port at the bottom of `config.yml`

    piestats web -c config.yml

Run stats update

    piestats update -c config.yml

Crontab example for running stats update every hour. Change paths accordingly!

    @hourly /home/pystats/soldat-pystats/env/bin/piestats update -c /home/pystats/soldat-pystats/config.yml

See the [webserver guide](WEBSERVER.md) if you want to remove the :5000 from the URLs.


# Contact
 - Joe Gillotti - <joe@u13.net>
 - [GitHub](https://github.com/jrgp/soldat-pystats)
 - License: MIT
