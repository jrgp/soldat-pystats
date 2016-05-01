## Install properly (deb package, apache vhost, update stats on cron)

Rather than running soldat-pystats under a virtualenv, it is easier to build and install a .deb package. This avoids needing to manually build a virtualenv and also makes using it under `mod_wsgi` nice and easy.

Tested on Ubuntu 14.04 LTS.

### Build & install debian package

Grab tools to build debs and compile Python modules as debs.

    sudo apt-get install dpkg-dev python-dev dh-virtualenv build-essential
    
Build soldat-pystats debian package (run this in the main git checkout folder)

	dpkg-buildpackage -us -uc 

Verify it exists (it will be small).

	$ ls -lh ../soldat-pystats*.deb
	-rw-r--r-- 1 joe joe 17M May  1 05:03 ../soldat-pystats_0.1_amd64.deb

Install it

	sudo dpkg -i ../soldat-pystats_0.1_amd64.deb

This will have installed the the app and all its python deps nicely contained under `/usr/share/python/soldat-pystats/`.

### Configure apache

This assumes you are familiar with the basics of running an apache web server on a debian-based OS.

Create wsgi folders & set secure permissions.

	sudo mkdir /var/www/soldat-pystats
	sudo chown www-data: /var/www/soldat-pystats
	sudo chmod 700 /var/www/soldat-pystats
	
Copy yaml config file & wsgi script. If you choose to put these files elsewhere, make sure you update the hardcoded paths in `pystats.wsgi`.

	sudo cp config.yml /var/www/soldat-pystats/config.yml
	sudo cp pystats.wsgi /var/www/soldat-pystats/pystats.wsgi
	
Get apache and wsgi module

	sudo apt-get install apache2 libapache2-mod-wsgi	
	
Configure your apache vhost. See `soldat-pystats-apache.conf` for an example.

Once your vhost is set, reload apache.

	sudo service apache2 reload	

### Run stats update under cron

You probably want your soldat servers to update stats automatically. Add a line such as the following to crontab (`sudo crontab -e`) to make stats update every hour. Make sure the path to your config file is accurate.

	@hourly /usr/share/python/soldat-pystats/bin/runupdate -c /var/www/soldat-pystats/config.yml


## Uninstall

	sudo apt-get remove soldat-pystats 