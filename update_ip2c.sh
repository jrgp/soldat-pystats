#!/bin/bash

# Grab latest ip2c database from maxmind and move it into place

set -e

cd "$(dirname "$0")"

curl -s https://geolite.maxmind.com/download/geoip/database/GeoLite2-Country.tar.gz | tar xzf -

mv -v GeoLite2-Country_*/GeoLite2-Country.mmdb piestats/update/GeoLite2-Country.mmdb

rm -rf GeoLite2-Country_*

echo Updated
