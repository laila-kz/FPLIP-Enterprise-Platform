@extends('layouts.app')

@section('title', "Investigation #{$investigation->id} - Machine {$investigation->machine_id}")

@section('content')
<div class="space-y-6">
    <!-- Breadcrumb & Investigation Header -->
    <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
            <div class="flex items-center space-x-2 text-xs font-semibold text-slate-400 mb-1">
                <a href="{{ route('investigations.dashboard') }}" class="hover:text-blue-600 transition">Dashboard</a>
                <span>/</span>
                <span class="text-slate-700">Investigation #{{ $investigation->id }}</span>
            </div>
            <div class="flex flex-wrap items-center gap-3 mt-1">
                <h1 class="text-2xl font-black text-slate-900 tracking-tight">
                    Machine {{ $investigation->machine_id }}
                </h1>
                
                <!-- Status Badge -->
                @php
                    $status = $investigation->status;
                    $statusBadge = match($status) {
                        'closed' => 'bg-emerald-50 text-emerald-700 border-emerald-200',
                        'pending_review' => 'bg-purple-50 text-purple-700 border-purple-200',
                        'assigned' => 'bg-blue-50 text-blue-700 border-blue-200',
                        default => 'bg-amber-50 text-amber-700 border-amber-200'
                    };
                    $sevBadge = match($investigation->severity) {
                        'high' => 'bg-red-50 text-red-700 border-red-200',
                        'medium' => 'bg-amber-50 text-amber-700 border-amber-200',
                        default => 'bg-blue-50 text-blue-700 border-blue-200'
                    };
                @endphp
                <span class="px-3 py-1 text-xs font-bold rounded-full uppercase tracking-wider border {{ $statusBadge }}">
                    {{ str_replace('_', ' ', $status) }}
                </span>

                <span class="px-3 py-1 text-xs font-bold rounded-full uppercase tracking-wider border {{ $sevBadge }}">
                    {{ $investigation->severity }} Severity
                </span>
            </div>
            <p class="text-xs text-slate-500 mt-2 font-mono">
                Signal: <strong class="text-slate-800">{{ strtoupper(str_replace('_', ' ', $investigation->signal_type)) }}</strong> • 
                Opened: {{ $investigation->opened_at->format('M d, Y H:i:s') }}
                @if($investigation->technician)
                    • Assigned: <strong class="text-blue-600">{{ $investigation->technician->name }}</strong>
                @endif
            </p>
        </div>

        <!-- Manager Quick Actions (Assign / Close) -->
        @if(auth()->user()->role === 'manager')
            <div class="flex flex-wrap items-center gap-2">
                @if($investigation->status === 'open')
                    <!-- Assign Technician Dropdown -->
                    <form method="POST" action="{{ route('investigations.assign', $investigation) }}" class="flex items-center space-x-2">
                        @csrf
                        <select name="technician_id" class="text-xs bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 font-medium text-slate-700 focus:ring-2 focus:ring-blue-500">
                            <option value="">Select Technician...</option>
                            @foreach($technicians as $tech)
                                <option value="{{ $tech->id }}">{{ $tech->name }}</option>
                            @endforeach
                        </select>
                        <button type="submit" class="text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg shadow-2xs transition active:scale-95 cursor-pointer">
                            Assign Work Order
                        </button>
                    </form>
                @elseif($investigation->status === 'pending_review' || $investigation->status === 'assigned')
                    <!-- Manager Approve & Close Form -->
                    <form method="POST" action="{{ route('investigations.close', $investigation) }}">
                        @csrf
                        <button type="submit" class="text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg shadow-2xs transition active:scale-95 cursor-pointer flex items-center space-x-1.5">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                            <span>Approve & Close Investigation</span>
                        </button>
                    </form>
                @endif
            </div>
        @endif
    </div>

    <!-- 2-Column Responsive Workbench Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <!-- LEFT COLUMN: Multi-Function Telemetry Graph, OEE Overview & ML Model -->
        <div class="space-y-6">
            <!-- Multi-Functional Interactive Telemetry & Physics Analyzer Graph -->
            <x-telemetry-chart :context="$context" :machineId="$investigation->machine_id" />

            <!-- Machine Live Telemetry & Loss Attribution -->
            <x-telemetry-overview :context="$context" />

            <!-- Scikit-Learn Predictive Scrap Risk Model -->
            <x-ml-predictor :mlRisk="$mlRisk" />
        </div>

        <!-- RIGHT COLUMN: Gemini AI Diagnostics, Technician Findings, and Lifecycle Timeline -->
        <div class="space-y-6">
            <!-- Gemini 3.5 Flash Lite Operational Diagnostic Card -->
            <x-ai-diagnostic :investigation="$investigation" :aiExplanation="$aiExplanation" />

            <!-- Technician Verified Findings Card (If Submitted) -->
            <x-finding-card :investigation="$investigation" />

            <!-- Technician Input Form (If Assigned / Pending Review) -->
            @if(in_array($investigation->status, ['assigned', 'pending_review']) && (auth()->user()->role === 'technician' || auth()->user()->role === 'manager'))
                <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6 space-y-4">
                    <div class="flex items-center space-x-2 pb-3 border-b border-slate-100">
                        <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                        <h3 class="text-base font-bold text-slate-900">
                            {{ $investigation->finding ? 'Update Root Cause Findings' : 'Submit Root Cause Findings & Corrective Action' }}
                        </h3>
                    </div>

                    <form method="POST" action="{{ route('technician.findings.submit', $investigation) }}" class="space-y-4">
                        @csrf
                        <div>
                            <label class="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
                                Root Cause Category <span class="text-red-500">*</span>
                            </label>
                            <select name="root_cause_category" required class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium text-slate-800 focus:ring-2 focus:ring-blue-500">
                                <option value="">Select Root Cause...</option>
                                @foreach(config('investigations.root_cause_categories', ['Tooling Wear', 'Mechanical Calibration', 'Operator Training', 'Raw Material Defect', 'Thermal Drift', 'Electrical / Sensor Noise', 'Software / PLC Fault', 'Maintenance Overdue', 'Other']) as $cat)
                                    <option value="{{ $cat }}" {{ (old('root_cause_category', $investigation->finding->root_cause_category ?? '') === $cat) ? 'selected' : '' }}>
                                        {{ $cat }}
                                    </option>
                                @endforeach
                            </select>
                        </div>

                        <div>
                            <label class="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
                                Detailed Physical Finding Description <span class="text-red-500">*</span>
                            </label>
                            <textarea name="root_cause_description" rows="3" required placeholder="Describe observed physical condition, sensor anomalies, wear patterns, or calibration drift..." class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-3 text-slate-800 focus:ring-2 focus:ring-blue-500 font-sans leading-relaxed">{{ old('root_cause_description', $investigation->finding->root_cause_description ?? '') }}</textarea>
                        </div>

                        <div>
                            <label class="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
                                Corrective Actions Taken <span class="text-red-500">*</span>
                            </label>
                            <textarea name="corrective_action" rows="3" required placeholder="Describe parts replaced, calibrations adjusted, lubrication applied, or machine settings reset..." class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-3 text-slate-800 focus:ring-2 focus:ring-blue-500 font-sans leading-relaxed">{{ old('corrective_action', $investigation->finding->corrective_action ?? '') }}</textarea>
                        </div>

                        <div class="flex justify-end pt-2">
                            <button type="submit" class="text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg shadow-2xs transition active:scale-95 cursor-pointer">
                                {{ $investigation->finding ? 'Update Findings' : 'Submit & Route for Manager Approval' }}
                            </button>
                        </div>
                    </form>
                </div>
            @endif

            <!-- Lifecycle & Audit Trail Component -->
            <x-audit-timeline :investigation="$investigation" />
        </div>
    </div>
</div>

<!-- AJAX AI Generation Script -->
<script>
async function runAiExplanation() {
    const btn = document.getElementById('btnAiExplain');
    const spinner = document.getElementById('aiSpinner');
    const btnText = document.getElementById('aiBtnText');
    const resultBox = document.getElementById('aiResultBox');
    const emptyPrompt = document.getElementById('aiEmptyPrompt');

    if (btn) btn.disabled = true;
    if (spinner) spinner.classList.remove('hidden');
    if (btnText) btnText.innerText = 'Analyzing with Gemini...';

    try {
        const response = await fetch("{{ route('investigations.explain', $investigation) }}", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': '{{ csrf_token() }}',
                'Accept': 'application/json'
            }
        });

        const data = await response.json();

        if (response.ok && data.success) {
            const ai = data.ai_explanation;
            
            if (emptyPrompt) emptyPrompt.classList.add('hidden');
            if (resultBox) resultBox.classList.remove('hidden');

            const summary = ai.summary || ai.explanation || 'No summary returned.';
            const engineering = ai.engineering_breakdown || null;
            const actions = ai.recommended_actions || [];
            const prevention = ai.preventative_measures || [];

            let html = `
                <div class="bg-indigo-50/60 border border-indigo-100 rounded-xl p-4">
                    <div class="text-xs font-semibold text-indigo-900 uppercase tracking-wider mb-1.5">Executive Summary</div>
                    <div class="text-sm text-indigo-950 font-medium leading-relaxed">${summary}</div>
                </div>
            `;

            if (engineering) {
                html += `
                    <div class="bg-slate-50 border border-slate-100 rounded-xl p-4">
                        <div class="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">Engineering Root Cause Analysis</div>
                        <div class="text-xs text-gray-800 leading-relaxed font-sans">${engineering}</div>
                    </div>
                `;
            }

            if (actions.length > 0) {
                html += `
                    <div>
                        <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Recommended Operational Actions</h4>
                        <div class="space-y-1.5">
                            ${actions.map(a => `
                                <div class="flex items-start text-xs text-gray-800 bg-gray-50 border border-gray-100 p-2.5 rounded-lg">
                                    <span class="text-indigo-600 font-bold mr-2 mt-0.5">➔</span>
                                    <span class="leading-relaxed">${a}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            if (prevention.length > 0) {
                html += `
                    <div>
                        <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Long-Term Preventative Countermeasures</h4>
                        <div class="space-y-1.5">
                            ${prevention.map(p => `
                                <div class="flex items-start text-xs text-emerald-900 bg-emerald-50/60 border border-emerald-100 p-2.5 rounded-lg">
                                    <span class="text-emerald-600 font-bold mr-2 mt-0.5">✔</span>
                                    <span class="leading-relaxed">${p}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            resultBox.innerHTML = html;
            if (btnText) btnText.innerText = 'Re-Generate AI Analysis';
        } else {
            alert('Failed to generate AI explanation: ' + (data.message || 'Unknown error.'));
            if (btnText) btnText.innerText = 'Explain This Anomaly';
        }
    } catch (err) {
        console.error('Gemini AI Diagnostic Error:', err);
        alert('Network error communicating with Gemini diagnostic service.');
        if (btnText) btnText.innerText = 'Explain This Anomaly';
    } finally {
        if (btn) btn.disabled = false;
        if (spinner) spinner.classList.add('hidden');
    }
}
</script>
@endsection
