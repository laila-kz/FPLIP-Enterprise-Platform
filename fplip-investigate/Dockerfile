FROM php:8.2-cli

# Install system dependencies & PHP extensions for Laravel & SQLite
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libsqlite3-dev \
    libzip-dev \
    libxml2-dev \
    unzip \
    && docker-php-ext-install pdo_sqlite zip xml bcmath \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /var/www/html

# Copy application files
COPY . .

# Ensure storage and bootstrap/cache permissions
RUN chmod -R 777 storage bootstrap/cache database

# Expose Laravel port
EXPOSE 8081

# Serve Laravel application
CMD ["php", "artisan", "serve", "--host=0.0.0.0", "--port=8081"]
