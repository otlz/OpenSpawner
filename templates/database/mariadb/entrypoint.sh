#!/bin/bash
set -e

DATA_DIR="/var/lib/mysql"

# Initialize MariaDB data directory on first run
if [ ! -d "${DATA_DIR}/mysql" ]; then
    echo "[MariaDB] Initialisiere Datenbank..."
    mysql_install_db --user=mysql --datadir="${DATA_DIR}" --auth-root-authentication-method=normal > /dev/null 2>&1
    echo "[MariaDB] Datenbank initialisiert."
fi

# Ensure mysqld runtime directory exists
mkdir -p /run/mysqld && chown mysql:mysql /run/mysqld

# Configure phpMyAdmin to use the correct password
cat > /etc/phpmyadmin/config-db.php <<-EOF
<?php
\$dbuser='root';
\$dbpass='root';
\$basepath='';
\$dbname='phpmyadmin';
\$dbserver='localhost';
\$dbport='';
\$dbtype='mysql';
EOF

# Configure phpMyAdmin auto-login and configuration storage
cat > /etc/phpmyadmin/conf.d/autologin.php <<-EOF
<?php
\$cfg['Servers'][1]['auth_type'] = 'config';
\$cfg['Servers'][1]['user'] = 'root';
\$cfg['Servers'][1]['password'] = 'root';
\$cfg['Servers'][1]['AllowNoPassword'] = false;

/* Configuration storage */
\$cfg['Servers'][1]['controluser'] = 'root';
\$cfg['Servers'][1]['controlpass'] = 'root';
\$cfg['Servers'][1]['pmadb'] = 'phpmyadmin';
\$cfg['Servers'][1]['bookmarktable'] = 'pma__bookmark';
\$cfg['Servers'][1]['relation'] = 'pma__relation';
\$cfg['Servers'][1]['table_info'] = 'pma__table_info';
\$cfg['Servers'][1]['table_coords'] = 'pma__table_coords';
\$cfg['Servers'][1]['pdf_pages'] = 'pma__pdf_pages';
\$cfg['Servers'][1]['column_info'] = 'pma__column_info';
\$cfg['Servers'][1]['history'] = 'pma__history';
\$cfg['Servers'][1]['recent'] = 'pma__recent';
\$cfg['Servers'][1]['favorite'] = 'pma__favorite';
\$cfg['Servers'][1]['table_uiprefs'] = 'pma__table_uiprefs';
\$cfg['Servers'][1]['tracking'] = 'pma__tracking';
\$cfg['Servers'][1]['userconfig'] = 'pma__userconfig';
\$cfg['Servers'][1]['users'] = 'pma__users';
\$cfg['Servers'][1]['usergroups'] = 'pma__usergroups';
\$cfg['Servers'][1]['navigationhiding'] = 'pma__navigationhiding';
\$cfg['Servers'][1]['savedsearches'] = 'pma__savedsearches';
\$cfg['Servers'][1]['central_columns'] = 'pma__central_columns';
\$cfg['Servers'][1]['designer_settings'] = 'pma__designer_settings';
\$cfg['Servers'][1]['export_templates'] = 'pma__export_templates';
EOF

mkdir -p /var/log/supervisor

exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
