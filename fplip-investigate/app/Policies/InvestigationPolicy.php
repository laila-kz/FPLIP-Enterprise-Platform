<?php

namespace App\Policies;

use App\Models\Investigation;
use App\Models\User;

/**
 * This is the enforcement layer, not a suggestion layer. Every method here
 * must be called from a controller via $this->authorize(...) or
 * Gate::authorize(...) BEFORE any state change — never trust that the UI
 * only shows the button to the right person. A direct, crafted request
 * from the wrong role or the wrong technician must be rejected here.
 */
class InvestigationPolicy
{
    /** Managers see everything. Technicians only ever see their own assigned/pending_review investigations. */
    public function viewAny(User $user): bool
    {
        return $user->isManager() || $user->isTechnician();
    }

    /**
     * Viewing a SINGLE investigation's detail page.
     * Manager: always allowed.
     * Technician: allowed only if this investigation is assigned to them —
     * NOT allowed just because they hold the technician role in general.
     */
    public function view(User $user, Investigation $investigation): bool
    {
        if ($user->isManager()) {
            return true;
        }

        return $user->isTechnician() && $investigation->assigned_to_id === $user->id;
    }

    /** Only a manager may open a new investigation from a live signal. */
    public function open(User $user): bool
    {
        return $user->isManager();
    }

    /**
     * Assign is manager-only AND requires the investigation to currently
     * be 'open' — the status check is deliberately duplicated here (not
     * just left to Investigation::assignTo()'s own guard) so that an
     * unauthorized attempt is rejected with a clean 403 before the model
     * layer is even reached, rather than surfacing as a transition-error
     * exception.
     */
    public function assign(User $user, Investigation $investigation): bool
    {
        return $user->isManager() && $investigation->status === 'open';
    }

    /** Close is manager-only AND requires 'pending_review'. */
    public function close(User $user, Investigation $investigation): bool
    {
        return $user->isManager() && $investigation->status === 'pending_review';
    }

    /**
     * Submitting findings: technician-only, must be THIS investigation's
     * assigned technician specifically (never "any technician"), and the
     * investigation must currently be 'assigned'.
     */
    public function submitFindings(User $user, Investigation $investigation): bool
    {
        return $user->isTechnician()
            && $investigation->assigned_to_id === $user->id
            && $investigation->status === 'assigned';
    }

    /**
     * Attaching evidence: the assigned technician (while the investigation
     * is still open/assigned to them) or any manager, at any point.
     */
    public function attachEvidence(User $user, Investigation $investigation): bool
    {
        if ($user->isManager()) {
            return true;
        }

        return $user->isTechnician()
            && $investigation->assigned_to_id === $user->id
            && in_array($investigation->status, ['assigned', 'pending_review'], true);
    }

    /**
     * Downloading an evidence file: the investigation's opener, its
     * assigned technician, or any manager — nobody else, regardless of
     * whether they can guess the storage path.
     */
    public function viewEvidence(User $user, Investigation $investigation): bool
    {
        if ($user->isManager()) {
            return true;
        }

        return $user->id === $investigation->opened_by_id
            || $user->id === $investigation->assigned_to_id;
    }

    /** Audit trail visibility mirrors view() — same people who can see the investigation can see its history. */
    public function viewAuditLog(User $user, Investigation $investigation): bool
    {
        return $this->view($user, $investigation);
    }
}
