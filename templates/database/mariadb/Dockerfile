# MariaDB + phpMyAdmin for learning SQL
FROM debian:bookworm-slim

ARG DEBIAN_FRONTEND=noninteractive

# Allow service commands during build (needed by phpmyadmin postinst)
RUN printf '#!/bin/sh\nexit 0\n' > /usr/sbin/policy-rc.d && \
    chmod +x /usr/sbin/policy-rc.d

RUN apt-get update && \
    # Pre-seed phpmyadmin debconf to skip interactive setup
    echo "phpmyadmin phpmyadmin/dbconfig-install boolean false" | debconf-set-selections && \
    echo "phpmyadmin phpmyadmin/reconfigure-webserver multiselect apache2" | debconf-set-selections && \
    apt-get install -y --no-install-recommends \
        mariadb-server \
        apache2 \
        libapache2-mod-php \
        php-mysql \
        php-mbstring \
        php-zip \
        php-gd \
        php-curl \
        phpmyadmin \
        supervisor \
    && rm -rf /var/lib/apt/lists/*

# Configure Apache to listen on port 8080 and serve phpMyAdmin at root
RUN sed -i 's/Listen 80$/Listen 8080/' /etc/apache2/ports.conf \
    && sed -i 's/<VirtualHost \*:80>/<VirtualHost *:8080>/' /etc/apache2/sites-enabled/000-default.conf \
    && sed -i 's|DocumentRoot /var/www/html|DocumentRoot /usr/share/phpmyadmin|' /etc/apache2/sites-enabled/000-default.conf \
    && echo '<Directory /usr/share/phpmyadmin>\n    AllowOverride All\n    Require all granted\n</Directory>' >> /etc/apache2/sites-enabled/000-default.conf

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY init.sql /etc/mysql/init.sql
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

CMD ["/entrypoint.sh"]
