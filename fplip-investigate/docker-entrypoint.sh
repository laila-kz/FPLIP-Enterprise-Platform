#!/bin/sh
set -e

echo "==> Initializing FPLIP Investigation Service..."

# Ensure .env file exists
if [ ! -f /var/www/html/.env ]; then
    if [ -f /var/www/html/.env.example ]; then
        echo "==> Copying .env.example to .env..."
        cp /var/www/html/.env.example /var/www/html/.env
    fi
fi

# Ensure application key is generated
if [ -f /var/www/html/.env ] && ! grep -q "^APP_KEY=base64:" /var/www/html/.env; then
    echo "==> Generating application key..."
    php artisan key:generate --force
fi

# Ensure storage and cache directory permissions
mkdir -p /var/www/html/storage/framework/cache/data \
         /var/www/html/storage/framework/sessions \
         /var/www/html/storage/framework/views \
         /var/www/html/storage/logs \
         /var/www/html/bootstrap/cache \
         /var/www/html/database

chmod -R 777 /var/www/html/storage \
             /var/www/html/bootstrap/cache \
             /var/www/html/database

# Ensure SQLite database file exists
if [ ! -f /var/www/html/database/database.sqlite ]; then
    echo "==> Creating database.sqlite..."
    touch /var/www/html/database/database.sqlite
    chmod 666 /var/www/html/database/database.sqlite
    NEW_DB=true
else
    NEW_DB=false
fi

# Run database migrations
echo "==> Running database migrations..."
php artisan migrate --force

# Seed database if newly created
if [ "$NEW_DB" = "true" ]; then
    echo "==> Fresh database detected. Running database seeder..."
    php artisan db:seed --force || true
fi

echo "==> Starting Laravel server on port 8081..."
exec "$@"
