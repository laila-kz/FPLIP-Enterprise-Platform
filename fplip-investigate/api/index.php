<?php

/**
 * Serverless Entry Point for Laravel on Vercel.
 * Dynamically configures the writable storage directory in /tmp
 * and prepares the SQLite database if needed.
 */

if (isset($_ENV['VERCEL']) || isset($_SERVER['VERCEL']) || getenv('VERCEL')) {
    $storageDir = '/tmp/storage';
    $subDirs = [
        $storageDir,
        $storageDir . '/framework',
        $storageDir . '/framework/views',
        $storageDir . '/framework/cache',
        $storageDir . '/framework/cache/data',
        $storageDir . '/framework/sessions',
        $storageDir . '/logs',
        $storageDir . '/app',
        $storageDir . '/app/public',
    ];

    foreach ($subDirs as $dir) {
        if (!is_dir($dir)) {
            @mkdir($dir, 0755, true);
        }
    }

    // Set Laravel storage path dynamically to /tmp/storage
    putenv("APP_STORAGE={$storageDir}");
    $_ENV['APP_STORAGE'] = $storageDir;
    $_SERVER['APP_STORAGE'] = $storageDir;

    // Handle SQLite database in /tmp for serverless runtime
    $tmpDb = '/tmp/database.sqlite';
    if (!file_exists($tmpDb)) {
        $sourceDb = dirname(__DIR__) . '/database/database.sqlite';
        if (file_exists($sourceDb) && filesize($sourceDb) > 0) {
            @copy($sourceDb, $tmpDb);
        } else {
            @touch($tmpDb);
        }
    }

    if (!getenv('DB_CONNECTION') || getenv('DB_CONNECTION') === 'sqlite') {
        putenv("DB_DATABASE={$tmpDb}");
        $_ENV['DB_DATABASE'] = $tmpDb;
        $_SERVER['DB_DATABASE'] = $tmpDb;
    }
}

require __DIR__ . '/../public/index.php';
