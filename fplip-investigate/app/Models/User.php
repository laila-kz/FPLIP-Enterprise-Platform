<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;

class User extends Authenticatable
{
    use HasFactory, Notifiable;

    protected $fillable = [
        'name',
        'email',
        'password',
        'role',
    ];

    protected $hidden = [
        'password',
        'remember_token',
    ];

    // Laravel 11 style: casts() as a method, not a $casts property.
    protected function casts(): array
    {
        return [
            'email_verified_at' => 'datetime',
            'password' => 'hashed',
        ];
    }

    public function isManager(): bool
    {
        return $this->role === 'manager';
    }

    public function isTechnician(): bool
    {
        return $this->role === 'technician';
    }

    /** Investigations this user opened. */
    public function openedInvestigations(): HasMany
    {
        return $this->hasMany(Investigation::class, 'opened_by_id');
    }

    /** Investigations currently assigned to this user. */
    public function assignedInvestigations(): HasMany
    {
        return $this->hasMany(Investigation::class, 'assigned_to_id');
    }

    public function findings(): HasMany
    {
        return $this->hasMany(Finding::class, 'technician_id');
    }

    public function uploadedEvidence(): HasMany
    {
        return $this->hasMany(Evidence::class, 'uploaded_by_id');
    }

    public function auditLogEntries(): HasMany
    {
        return $this->hasMany(AuditLog::class, 'actor_id');
    }
}
