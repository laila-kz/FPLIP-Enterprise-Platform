@props(['investigation', 'aiExplanation'])

<div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-5">
    <div class="flex items-center justify-between pb-3 border-b border-gray-100">
        <div class="flex items-center space-x-2">
            <svg class="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>
            <h3 class="text-base font-bold text-gray-900">Gemini AI Operational Diagnostic</h3>
        </div>
        <div class="flex items-center space-x-2">
            <span class="text-xs font-mono bg-indigo-50 text-indigo-700 font-semibold px-2.5 py-1 rounded-md">gemini-3.5-flash-lite</span>
            <button id="btnAiExplain" onclick="runAiExplanation()" type="button" class="inline-flex items-center text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1.5 rounded-lg transition active:scale-95 shadow-sm cursor-pointer">
                <svg id="aiSpinner" class="hidden animate-spin -ml-0.5 mr-1.5 h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                <span id="aiBtnText">{{ $aiExplanation ? 'Re-Generate AI Analysis' : 'Explain This Anomaly' }}</span>
            </button>
        </div>
    </div>

    <!-- AI Result Container -->
    <div id="aiResultBox" class="{{ $aiExplanation ? '' : 'hidden' }} space-y-4">
        @if($aiExplanation)
            @php
                $summary = $aiExplanation['summary'] ?? ($aiExplanation['explanation'] ?? '');
                $actions = $aiExplanation['recommended_actions'] ?? [];
                $engineering = $aiExplanation['engineering_breakdown'] ?? null;
                $prevention = $aiExplanation['preventative_measures'] ?? [];
            @endphp

            <!-- Executive Summary -->
            <div class="bg-indigo-50/60 border border-indigo-100 rounded-xl p-4">
                <div class="text-xs font-semibold text-indigo-900 uppercase tracking-wider mb-1.5">Executive Summary</div>
                <div class="text-sm text-indigo-950 font-medium leading-relaxed" id="aiSummaryText">
                    {{ $summary }}
                </div>
            </div>

            <!-- Engineering Breakdown if available -->
            @if($engineering)
                <div class="bg-slate-50 border border-slate-100 rounded-xl p-4" id="aiEngineeringBox">
                    <div class="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">Engineering Root Cause Analysis</div>
                    <div class="text-xs text-gray-800 leading-relaxed font-sans" id="aiEngineeringText">
                        {{ $engineering }}
                    </div>
                </div>
            @endif

            <!-- Recommended Actions -->
            @if(count($actions) > 0)
                <div id="aiActionsContainer">
                    <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Recommended Operational Actions</h4>
                    <div class="space-y-1.5" id="aiActionsList">
                        @foreach($actions as $action)
                            <div class="flex items-start text-xs text-gray-800 bg-gray-50 border border-gray-100 p-2.5 rounded-lg">
                                <span class="text-indigo-600 font-bold mr-2 mt-0.5">➔</span>
                                <span class="leading-relaxed">{{ $action }}</span>
                            </div>
                        @endforeach
                    </div>
                </div>
            @endif

            <!-- Preventative Measures -->
            @if(count($prevention) > 0)
                <div id="aiPreventionContainer">
                    <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Long-Term Preventative Countermeasures</h4>
                    <div class="space-y-1.5" id="aiPreventionList">
                        @foreach($prevention as $prev)
                            <div class="flex items-start text-xs text-emerald-900 bg-emerald-50/60 border border-emerald-100 p-2.5 rounded-lg">
                                <span class="text-emerald-600 font-bold mr-2 mt-0.5">✔</span>
                                <span class="leading-relaxed">{{ $prev }}</span>
                            </div>
                        @endforeach
                    </div>
                </div>
            @endif
        @else
            <!-- Dynamic placeholder filled by AJAX -->
            <div id="aiDynamicContent" class="space-y-3"></div>
        @endif
    </div>

    <!-- Empty State Prompt if not yet generated -->
    <div id="aiEmptyPrompt" class="{{ $aiExplanation ? 'hidden' : '' }} text-center py-6 bg-slate-50 rounded-xl border border-dashed border-gray-200">
        <svg class="w-8 h-8 text-gray-300 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
        <p class="text-xs text-gray-500 font-medium">Click "Explain This Anomaly" to perform real-time Gemini AI diagnostic synthesis.</p>
    </div>
</div>
