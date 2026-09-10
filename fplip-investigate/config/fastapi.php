<?php

return [
    'base_url' => env('FASTAPI_BASE_URL', 'http://localhost:8000'),
    'api_key' => env('INTERNAL_API_KEY', env('FASTAPI_API_KEY')),
    'timeout' => (int) env('FASTAPI_TIMEOUT', 90),
];