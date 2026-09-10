# ==========================================
# Stage 1: Build Frontend Assets (Vite / Tailwind / JS)
# ==========================================
FROM node:20-alpine AS frontend
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci || npm install --no-audit

COPY resources/ ./resources/
COPY public/ ./public/
COPY vite.config.js postcss.config.js tailwind.config.js ./
RUN npm run build

# ==========================================
# Stage 2: PHP Application Runtime
# ==========================================
FROM php:8.2-cli

# Install system dependencies and PHP extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    libsqlite3-dev \
    libzip-dev \
    libxml2-dev \
    unzip \
    && docker-php-ext-install pdo_sqlite zip xml bcmath \
    && curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /var/www/html

# Install Composer dependencies first for layer caching
COPY composer.json composer.lock ./
RUN composer install --no-interaction --prefer-dist --no-progress --no-scripts --optimize-autoloader

# Copy application source code
COPY . .

# Copy compiled frontend assets from frontend build stage
COPY --from=frontend /app/public/build ./public/build

# Setup entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && chmod -R 777 storage bootstrap/cache database

EXPOSE 8081

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["php", "artisan", "serve", "--host=0.0.0.0", "--port=8081"]

