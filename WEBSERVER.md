# Run soldat-pystats behind a web server

If you don't want the port to be shown in the URL, you can reverse-proxy pystats behind Apache or Nginx.


## Apache

First enable the reverse proxy and deflate modules:

    a2enmod proxy
    a2enmod proxy_http
    a2enmod deflate

Example Apache virtualhost to reverse proxy to a local pystats on port 5000:

```apache
<VirtualHost *:80>
        ServerName yourdomain.com

        ErrorLog /var/log/apache2/yourdomain.com.error
        CustomLog /var/log/apache2/yourdomain.com.access combined

        ProxyPass / "http://localhost:5000/" retry=0 timeout=5

        AddOutputFilterByType DEFLATE text/html application/json application/javascript text/css
</VirtualHost>

```

## Nginx

Nginx is a bit simpler than apache. Here is an example nginx vhost/server:

```nginx
server {
        listen 80 default_server;
        listen [::]:80 default_server;

        server_name yourdomain.com;

        location / {

            proxy_pass         http://localhost:5000/;
            proxy_redirect     off;

            gzip on;
            gzip_types application/json application/javascript text/css;
        }
}
```
