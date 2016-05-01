#
# Apache mod_wsgi config example
# --
#

# Gain access to our soldat-pystats installation
activate_this = '/usr/share/python/soldat-pystats/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

# Grab some dependencies
from piestats.config import Config
import redis

# mod_wsgi needs app to be named application
from piestats.web import app as application

# Initialize our pystats config object
config = Config('/var/www/soldat-pystats/config.yml')

# Start a persistent redis connection pool and throw it in our config for
# convenient access
config.redis_connection_pool = redis.ConnectionPool(**config.redis_connect)
application.config['config'] = config
