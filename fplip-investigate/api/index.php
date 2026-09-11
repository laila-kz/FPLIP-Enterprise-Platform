<?php
 
/**
 * Serverless Entry Point for Laravel on Vercel.
 * Dynamically configures the writable storage directory in /tmp
 * and prepares the SQLite database if needed.
 */

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

// Set Laravel bootstrap cache files to writable /tmp
$cacheDir = $storageDir . '/framework/cache';
putenv("APP_SERVICES_CACHE={$cacheDir}/services.php");
$_ENV['APP_SERVICES_CACHE'] = "{$cacheDir}/services.php";
$_SERVER['APP_SERVICES_CACHE'] = "{$cacheDir}/services.php";

putenv("APP_PACKAGES_CACHE={$cacheDir}/packages.php");
$_ENV['APP_PACKAGES_CACHE'] = "{$cacheDir}/packages.php";
$_SERVER['APP_PACKAGES_CACHE'] = "{$cacheDir}/packages.php";

putenv("APP_CONFIG_CACHE={$cacheDir}/config.php");
$_ENV['APP_CONFIG_CACHE'] = "{$cacheDir}/config.php";
$_SERVER['APP_CONFIG_CACHE'] = "{$cacheDir}/config.php";

putenv("APP_ROUTES_CACHE={$cacheDir}/routes-v7.php");
$_ENV['APP_ROUTES_CACHE'] = "{$cacheDir}/routes-v7.php";
$_SERVER['APP_ROUTES_CACHE'] = "{$cacheDir}/routes-v7.php";

putenv("APP_EVENTS_CACHE={$cacheDir}/events.php");
$_ENV['APP_EVENTS_CACHE'] = "{$cacheDir}/events.php";
$_SERVER['APP_EVENTS_CACHE'] = "{$cacheDir}/events.php";

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

// Fallback and sanitize APP_KEY
$appKey = trim(trim((string) (getenv('APP_KEY') ?: ($_ENV['APP_KEY'] ?? $_SERVER['APP_KEY'] ?? '')), '"\''));
$validKey = false;
if (str_starts_with($appKey, 'base64:')) {
    $decoded = base64_decode(substr($appKey, 7), true);
    if ($decoded !== false && strlen($decoded) === 32) {
        $validKey = true;
    }
} elseif (strlen($appKey) === 32) {
    $validKey = true;
}

if (!$validKey) {
    $appKey = 'base64:Q2AKsKuCjmMzeH87Y1zyGSREKtVZdYt6vv5UK/wB3jc=';
}

putenv("APP_KEY={$appKey}");
$_ENV['APP_KEY'] = $appKey;
$_SERVER['APP_KEY'] = $appKey;

// Enforce HTTPS in server environment
$_SERVER['HTTPS'] = 'on';
putenv("HTTPS=on");
$_ENV['HTTPS'] = 'on';

// Default session driver to cookie for stateless serverless if not set
if (!getenv('SESSION_DRIVER')) {
    putenv("SESSION_DRIVER=cookie");
    $_ENV['SESSION_DRIVER'] = 'cookie';
    $_SERVER['SESSION_DRIVER'] = 'cookie';
}

require __DIR__ . '/../public/index.php';

