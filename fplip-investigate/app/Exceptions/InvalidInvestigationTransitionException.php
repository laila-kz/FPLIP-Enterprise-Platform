<?php

namespace App\Exceptions;

use Exception;

/**
 * Thrown when a lifecycle transition is attempted from a status that
 * doesn't permit it (e.g. assigning an investigation that's already
 * assigned, or closing one that isn't pending_review). Controllers should
 * catch this and return a 409, never let it surface as a raw 500.
 */
class InvalidInvestigationTransitionException extends Exception
{
    //
}
