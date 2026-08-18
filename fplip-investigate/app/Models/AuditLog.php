<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class AuditLog extends Model
{
    // No factory: audit log rows are only ever created by
    // Investigation's lifecycle methods, never directly or in seeders
    // pretending to be organic activity — see DatabaseSeeder for how
    // sample audit trails are produced (by calling the real lifecycle
    // methods, not by inserting rows by hand).

    public $timestamps = false; // append-only: created_at is set explicitly, no updated_at exists

    protected $fillable = [
        'investigation_id',
        'actor_id',
        'event_type',
        'description',
        'metadata',
    ];

    protected function casts(): array
    {
        return [
            'metadata' => 'array',
            'created_at' => 'datetime',
        ];
    }

    protected static function booted(): void
    {
        static::creating(function (AuditLog $log) {
            $log->created_at ??= now();
        });
    }

    public function investigation(): BelongsTo
    {
        return $this->belongsTo(Investigation::class);
    }

    public function actor(): BelongsTo
    {
        return $this->belongsTo(User::class, 'actor_id');
    }
}
