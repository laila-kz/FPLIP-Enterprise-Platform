<?php

namespace App\Models;

use App\Exceptions\InvalidInvestigationTransitionException;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\HasOne;
use Illuminate\Support\Facades\DB;

class Investigation extends Model
{
    use HasFactory;

    protected $fillable = [
        'machine_id',
        'signal_type',
        'severity',
        'status',
        'evidence_snapshot',
        'opened_by_id',
        'assigned_to_id',
        'opened_at',
        'assigned_at',
        'closed_at',
    ];

    protected function casts(): array
    {
        return [
            'evidence_snapshot' => 'array',
            'opened_at' => 'datetime',
            'assigned_at' => 'datetime',
            'closed_at' => 'datetime',
        ];
    }

    // ---- Relationships ----

    public function openedBy(): BelongsTo
    {
        return $this->belongsTo(User::class, 'opened_by_id');
    }

    public function technician(): BelongsTo
    {
        return $this->belongsTo(User::class, 'assigned_to_id');
    }

    public function finding(): HasOne
    {
        return $this->hasOne(Finding::class);
    }

    public function evidence(): HasMany
    {
        return $this->hasMany(Evidence::class);
    }

    public function auditLogs(): HasMany
    {
        return $this->hasMany(AuditLog::class)->orderBy('created_at');
    }

    // ---- Query scopes ----

    /** Investigations currently assigned to a specific user, in an active state. */
    public function scopeAssignedTo($query, User $user)
    {
        return $query->where('assigned_to_id', $user->id)
            ->whereIn('status', ['assigned', 'pending_review']);
    }

    // ---- Lifecycle transitions ----
    // Each method is the single place a given transition can happen. Every
    // one: (1) guards the current status explicitly, (2) performs its state
    // change and audit log write atomically, (3) throws on an invalid
    // transition rather than silently no-op'ing. Controllers call these —
    // they never set `status` directly.

    public static function openFor(
        string $machineId,
        string $signalType,
        string $severity,
        array $evidenceSnapshot,
        User $openedBy,
    ): self {
        return DB::transaction(function () use ($machineId, $signalType, $severity, $evidenceSnapshot, $openedBy) {
            $investigation = self::create([
                'machine_id' => $machineId,
                'signal_type' => $signalType,
                'severity' => $severity,
                'status' => 'open',
                'evidence_snapshot' => $evidenceSnapshot,
                'opened_by_id' => $openedBy->id,
                'opened_at' => now(),
            ]);

            $investigation->auditLogs()->create([
                'actor_id' => $openedBy->id,
                'event_type' => 'opened',
                'description' => "Investigation opened by {$openedBy->name}.",
            ]);

            return $investigation;
        });
    }

    public function assignTo(User $technician, User $actor): void
    {
        if ($this->status !== 'open') {
            throw new InvalidInvestigationTransitionException(
                "Cannot assign investigation #{$this->id}: current status is '{$this->status}', expected 'open'."
            );
        }

        if (! $technician->isTechnician()) {
            throw new InvalidInvestigationTransitionException(
                "User #{$technician->id} does not have the technician role and cannot be assigned."
            );
        }

        DB::transaction(function () use ($technician, $actor) {
            $this->update([
                'assigned_to_id' => $technician->id,
                'assigned_at' => now(),
                'status' => 'assigned',
            ]);

            $this->auditLogs()->create([
                'actor_id' => $actor->id,
                'event_type' => 'assigned',
                'description' => "Assigned to {$technician->name} by {$actor->name}.",
                'metadata' => ['assigned_to_id' => $technician->id, 'assigned_to_name' => $technician->name],
            ]);
        });
    }

    /**
     * Records the technician's finding and moves the investigation into
     * pending_review, atomically. $findingData must already be validated
     * by the caller (root_cause_category, corrective_action, notes).
     */
    public function recordFinding(array $findingData, User $technician): Finding
    {
        if ($this->status !== 'assigned') {
            throw new InvalidInvestigationTransitionException(
                "Cannot submit findings for investigation #{$this->id}: current status is '{$this->status}', expected 'assigned'."
            );
        }

        if ($this->assigned_to_id !== $technician->id) {
            throw new InvalidInvestigationTransitionException(
                "Investigation #{$this->id} is not assigned to user #{$technician->id}."
            );
        }

        return DB::transaction(function () use ($findingData, $technician) {
            $finding = $this->finding()->create([
                ...$findingData,
                'technician_id' => $technician->id,
                'submitted_at' => now(),
            ]);

            $this->update(['status' => 'pending_review']);

            $this->auditLogs()->create([
                'actor_id' => $technician->id,
                'event_type' => 'finding_submitted',
                'description' => "Finding submitted by {$technician->name}.",
            ]);

            return $finding;
        });
    }

    public function close(User $actor): void
    {
        if ($this->status !== 'pending_review') {
            throw new InvalidInvestigationTransitionException(
                "Cannot close investigation #{$this->id}: current status is '{$this->status}', expected 'pending_review'."
            );
        }

        DB::transaction(function () use ($actor) {
            $this->update([
                'status' => 'closed',
                'closed_at' => now(),
            ]);

            $this->auditLogs()->create([
                'actor_id' => $actor->id,
                'event_type' => 'closed',
                'description' => "Closed by {$actor->name}.",
            ]);
        });
    }
}
