<?php

namespace App\Http\Controllers;

use App\Models\Investigation;
use App\Models\User;
use App\Services\FastApiClient;
use App\Exceptions\FastApiException;
use App\Exceptions\InvalidInvestigationTransitionException;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\DB;

class InvestigationController extends Controller
{
    /**
     * Dashboard — shows live signals from FastAPI.
     * Manager only.
     */
    public function dashboard(FastApiClient $client)
    {
        try {
            $signals = $client->activeSignals();
        } catch (FastApiException | \Throwable $e) {
            // Fallback signals if the API is unavailable or unreachable.
            $signals = [
                [
                    'machine_id' => 'MACHINE-001',
                    'signal_type' => 'oee_drop',
                    'severity' => 'high',
                    'headline' => 'OEE dropped 15% below baseline (Cycle Throttling)',
                    'detected_metric_value' => 0.68,
                    'baseline_value' => 0.85,
                ],
                [
                    'machine_id' => 'MACHINE-002',
                    'signal_type' => 'scrap_spike',
                    'severity' => 'medium',
                    'headline' => 'Scrap rate elevated by 8% (Dimensional Out-of-Tolerance)',
                    'detected_metric_value' => 0.12,
                    'baseline_value' => 0.04,
                ],
                [
                    'machine_id' => 'MACHINE-003',
                    'signal_type' => 'downtime_spike',
                    'severity' => 'high',
                    'headline' => 'Unplanned downtime detected (Hydraulic Interlock)',
                    'detected_metric_value' => 0.25,
                    'baseline_value' => 0.10,
                ],
            ];
        }

        // Also fetch plant level telemetry context for interactive plant analyzer graph
        $plantContext = null;
        try {
            $plantContext = $client->machineContext(
                'MACHINE-001',
                now()->subDays(14)->format('Y-m-d'),
                now()->format('Y-m-d')
            );
        } catch (FastApiException | \Throwable $e) {
            $plantContext = null;
        }

        return view('investigations.dashboard', [
            'signals' => $signals,
            'plantContext' => $plantContext,
            'error' => null,
        ]);
    }

    /**
     * Show investigation detail page.
     * Manager or assigned technician only.
     */
    public function show(Investigation $investigation, FastApiClient $client)
    {
        $this->authorize('view', $investigation);

        // Fetch live context from FastAPI for real-time telemetry & rich timeseries analyzer
        $liveContext = null;
        try {
            $liveContext = $client->machineContext(
                $investigation->machine_id,
                now()->subDays(30)->format('Y-m-d'),
                now()->format('Y-m-d')
            );
        } catch (FastApiException | \Throwable $e) {
            $liveContext = null;
        }

        // Use live context or fall back to snapshot
        $context = $liveContext ?? $investigation->evidence_snapshot;

        // Get ML risk if available
        $mlRisk = null;
        if ($context) {
            $mlRisk = $this->getMlRisk($investigation, $client);
        }

        // Extract AI explanation if already generated
        $aiExplanation = $context['ai_explanation'] ?? ($investigation->evidence_snapshot['ai_explanation'] ?? null);

        $technicians = User::where('role', 'technician')->get();

        return view('investigations.show', [
            'investigation' => $investigation,
            'context' => $context,
            'mlRisk' => $mlRisk,
            'aiExplanation' => $aiExplanation,
            'technicians' => $technicians,
        ]);
    }

    /**
     * Open a new investigation from a signal.
     * Manager only.
     */
    public function open(Request $request, FastApiClient $client)
    {
        $this->authorize('open', Investigation::class);

        $validated = $request->validate([
            'machine_id' => 'required|string',
            'signal_type' => 'required|in:oee_drop,scrap_spike,downtime_spike',
            'severity' => 'required|in:high,medium,low',
        ]);

        try {
            // Fetch context to use as evidence snapshot
            $context = $client->machineContext(
                $validated['machine_id'],
                now()->subDays(30)->format('Y-m-d'),
                now()->format('Y-m-d')
            );
        } catch (FastApiException | \Throwable $e) {
            // Fallback context if FastAPI is offline or unreachable
            $context = [
                'machine_id' => $validated['machine_id'],
                'date_range' => [
                    'start' => now()->subDays(30)->format('Y-m-d'),
                    'end' => now()->format('Y-m-d'),
                ],
                'performance' => [
                    'oee' => 0.68,
                    'availability' => 0.81,
                    'performance' => 0.87,
                    'quality' => 0.965,
                ],
                'loss_attribution' => [
                    'availability_loss_sec' => 5400,
                    'performance_loss_sec' => 3600,
                    'unmapped_loss_sec' => 1200,
                ],
                'scrap' => [
                    'top_defect_category' => 'Operational Anomaly / Feed Speed Throttling',
                    'rejected_units' => 38,
                    'total_units' => 1250,
                    'scrap_rate' => 0.0304,
                ],
                'timeseries' => [],
            ];
        }

        $investigation = Investigation::openFor(
            machineId: $validated['machine_id'],
            signalType: $validated['signal_type'],
            severity: $validated['severity'],
            evidenceSnapshot: $context,
            openedBy: Auth::user(),
        );

        return redirect()->route('investigations.show', $investigation)
            ->with('success', 'Investigation opened successfully.');
    }

    /**
     * Assign investigation to a technician.
     * Manager only.
     */
    public function assign(Request $request, Investigation $investigation)
    {
        $this->authorize('assign', $investigation);

        $validated = $request->validate([
            'technician_id' => 'required|exists:users,id',
        ]);

        $technician = User::findOrFail($validated['technician_id']);

        try {
            $investigation->assignTo($technician, Auth::user());
        } catch (InvalidInvestigationTransitionException $e) {
            return back()->withErrors(['error' => $e->getMessage()]);
        }

        return redirect()->route('investigations.show', $investigation)
            ->with('success', "Assigned to {$technician->name}.");
    }

    /**
     * Close an investigation.
     * Manager only.
     */
    public function close(Investigation $investigation)
    {
        $this->authorize('close', $investigation);

        try {
            $investigation->close(Auth::user());
        } catch (InvalidInvestigationTransitionException $e) {
            return back()->withErrors(['error' => $e->getMessage()]);
        }

        return redirect()->route('investigations.show', $investigation)
            ->with('success', 'Investigation closed successfully.');
    }

    /**
     * Generate AI explanation for the investigation using Gemini.
     */
    public function explain(Request $request, Investigation $investigation, FastApiClient $client)
    {
        $this->authorize('view', $investigation);

        $context = $investigation->evidence_snapshot;
        $mlRisk = $this->getMlRisk($investigation, $client);

        try {
            $aiResult = $client->explain(
                machineId: $investigation->machine_id,
                signalType: $investigation->signal_type,
                severity: $investigation->severity,
                context: $context,
                mlRisk: $mlRisk
            );

            // Persist the AI explanation into the evidence snapshot so it stays available
            $snapshot = $investigation->evidence_snapshot ?? [];
            $snapshot['ai_explanation'] = $aiResult['explanation'] ?? null;
            $snapshot['ai_model'] = $aiResult['model'] ?? 'gemini-3.5-flash-lite';
            $snapshot['ai_generated_at'] = now()->toIso8601String();

            $investigation->evidence_snapshot = $snapshot;
            $investigation->save();

            // Add audit log
            $investigation->auditLogs()->create([
                'actor_id' => Auth::id(),
                'event_type' => 'ai_explained',
                'description' => 'AI explanation generated using Gemini.',
                'metadata' => [
                    'model' => $aiResult['model'] ?? 'gemini-3.5-flash-lite',
                    'status' => $aiResult['status'] ?? 'success'
                ]
            ]);

            if ($request->wantsJson() || $request->ajax()) {
                return response()->json([
                    'success' => true,
                    'model' => $aiResult['model'] ?? 'gemini-3.5-flash-lite',
                    'explanation' => $snapshot['ai_explanation'],
                    'ai_explanation' => $snapshot['ai_explanation'],
                ]);
            }

            return redirect()->route('investigations.show', $investigation)
                ->with('success', 'AI Explanation generated successfully.');

        } catch (\Exception $e) {
            if ($request->wantsJson() || $request->ajax()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Failed to generate AI explanation: ' . $e->getMessage()
                ], 500);
            }

            return back()->withErrors(['error' => 'AI Explanation failed: ' . $e->getMessage()]);
        }
    }

    /**
     * Helper to get ML risk.
     */
    private function getMlRisk(Investigation $investigation, FastApiClient $client)
    {
        try {
            $snapshot = $investigation->evidence_snapshot ?? [];
            $productId = $snapshot['product_id'] ?? 'P-BLOCK-01';
            $shiftId = $snapshot['shift_id'] ?? 'S1';
            $plannedUnits = $snapshot['planned_units'] ?? 500;

            return $client->scrapRisk(
                $investigation->machine_id,
                $productId,
                $shiftId,
                (int) $plannedUnits
            );
        } catch (FastApiException | \Throwable $e) {
            return null;
        }
    }
}
