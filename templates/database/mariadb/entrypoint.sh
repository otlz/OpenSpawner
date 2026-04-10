#!/bin/bash
set -e

DATA_DIR="/var/lib/mysql"

# Initialize MariaDB data directory on first run
if [ ! -d "${DATA_DIR}/mysql" ]; then
    echo "[MariaDB] Initialisiere Datenbank..."
    mysql_install_db --user=mysql --datadir="${DATA_DIR}" > /dev/null 2>&1

    # Start MariaDB temporarily to configure it
    mysqld_safe --user=mysql --datadir="${DATA_DIR}" &
    MYSQL_PID=$!

    # Wait for MariaDB to be ready
    for i in $(seq 1 30); do
        if mysqladmin ping --silent 2>/dev/null; then
            break
        fi
        sleep 1
    done

    # Set root password and create student database
    mysql -u root <<-EOSQL
        ALTER USER 'root'@'localhost' IDENTIFIED BY 'root';
        DELETE FROM mysql.user WHERE User='';
        DROP DATABASE IF EXISTS test;
        CREATE DATABASE IF NOT EXISTS student_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        GRANT ALL PRIVILEGES ON student_db.* TO 'root'@'localhost';
        FLUSH PRIVILEGES;
EOSQL

    echo "[MariaDB] Setup abgeschlossen."
    kill $MYSQL_PID
    wait $MYSQL_PID 2>/dev/null || true
fi

# Configure phpMyAdmin to use the correct password
cat > /etc/phpmyadmin/config-db.php <<-EOF
<?php
\$dbuser='root';
\$dbpass='root';
\$basepath='';
\$dbname='phpmyadmin';
\$dbserver='localhost';
\$dbport='3306';
\$dbtype='mysql';
EOF

mkdir -p /var/log/supervisor

exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
