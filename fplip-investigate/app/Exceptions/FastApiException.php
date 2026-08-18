<?php

namespace App\Exceptions;

use Exception;

class FastApiException extends Exception
{
    public function __construct(string $message = 'FastAPI error', int $code = 0, ?Exception $previous = null)
    {
        parent::__construct($message, $code, $previous);
    }
}