<?php

namespace App\Http\Controllers;

use App\Models\Investigation;
use App\Models\Finding;
use App\Exceptions\InvalidInvestigationTransitionException;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Storage;

class TechnicianController extends Controller
{
    /**
     * My Tasks — assigned investigations.
     * Technician only.
     */
    public function myTasks()
    {
        $user = Auth::user();

        $query = Investigation::query();
        if ($user->isTechnician()) {
            $query->assignedTo($user);
        } else {
            $query->whereIn('status', ['assigned', 'pending_review']);
        }

        $investigations = $query
            ->with(['openedBy', 'finding'])
            ->orderBy('created_at', 'desc')
            ->get();

        return view('technician.tasks', [
            'investigations' => $investigations,
        ]);
    }

    /**
     * Submit findings for an investigation.
     * Technician only.
     */
    public function submitFindings(Request $request, Investigation $investigation)
    {
        $this->authorize('submitFindings', $investigation);

        $validated = $request->validate([
            'root_cause_category' => ['required', 'string', 'in:' . implode(',', config('investigations.root_cause_categories'))],
            'corrective_action' => 'required|string|max:1000',
            'notes' => 'nullable|string|max:1000',
            'evidence_photo' => 'nullable|image|mimes:jpg,jpeg,png|max:5120',
        ]);

        $evidencePath = null;
        if ($request->hasFile('evidence_photo')) {
            $path = $request->file('evidence_photo')->store('evidence', 'local');
            $evidencePath = $path;
        }

        try {
            $finding = $investigation->recordFinding(
                [
                    'root_cause_category' => $validated['root_cause_category'],
                    'corrective_action' => $validated['corrective_action'],
                    'notes' => $validated['notes'] ?? null,
                ],
                Auth::user()
            );

            // If evidence was uploaded, create evidence record
            if ($evidencePath) {
                $investigation->evidence()->create([
                    'finding_id' => $finding->id,
                    'uploaded_by_id' => Auth::id(),
                    'file_path' => $evidencePath,
                    'file_name' => $request->file('evidence_photo')->getClientOriginalName(),
                    'mime_type' => $request->file('evidence_photo')->getMimeType(),
                    'file_size_bytes' => $request->file('evidence_photo')->getSize(),
                    'uploaded_at' => now(),
                ]);
            }
        } catch (InvalidInvestigationTransitionException $e) {
            return back()->withErrors(['error' => $e->getMessage()]);
        }

        return redirect()->route('investigations.show', $investigation)
            ->with('success', 'Findings submitted successfully.');
    }
}
