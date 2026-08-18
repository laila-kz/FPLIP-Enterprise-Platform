<?php

namespace App\Providers;

use App\Models\Investigation;
use App\Policies\InvestigationPolicy;
use Illuminate\Foundation\Support\Providers\AuthServiceProvider as ServiceProvider;

/**
 * Laravel 11's policy auto-discovery would actually find InvestigationPolicy
 * on its own, since it follows the {Model}Policy naming convention in the
 * standard namespaces. It's registered explicitly here anyway — for a
 * security-critical mapping like this one, "the framework should find it
 * automatically" is a worse guarantee than "it's declared in one place,
 * verifiable by reading this file."
 *
 * Laravel 11 no longer ships this provider by default — create this file,
 * then register it in bootstrap/providers.php:
 *
 *     return [
 *         App\Providers\AppServiceProvider::class,
 *         App\Providers\AuthServiceProvider::class,
 *     ];
 */
class AuthServiceProvider extends ServiceProvider
{
    protected $policies = [
        Investigation::class => InvestigationPolicy::class,
    ];

    public function boot(): void
    {
        //
    }
}
