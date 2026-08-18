@props(['investigation'])

@php
    $finding = $investigation->finding;
@endphp

@if($finding)
    <div class="bg-white rounded-xl shadow-sm border border-emerald-200/80 p-6 border-l-4 border-l-emerald-500 space-y-4">
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
            <div class="flex items-center space-x-2">
                <div class="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-bold">
                    ✓
                </div>
                <h3 class="text-base font-bold text-gray-900">Technician Findings & Corrective Action</h3>
            </div>
            <span class="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                Verified
            </span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="bg-slate-50 border border-slate-100 p-3.5 rounded-xl">
                <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Identified Root Cause Category</span>
                <div class="text-sm font-bold text-gray-900 mt-1">
                    {{ $finding->root_cause_category ?? 'Unspecified' }}
                </div>
            </div>

            <div class="bg-slate-50 border border-slate-100 p-3.5 rounded-xl">
                <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Investigating Technician</span>
                <div class="text-sm font-bold text-gray-900 mt-1">
                    {{ $finding->technician->name ?? 'Technician' }}
                    <span class="text-xs text-gray-400 font-normal font-mono block">Submitted {{ $finding->created_at->format('M d, Y H:i') }}</span>
                </div>
            </div>
        </div>

        <div class="space-y-3 pt-1">
            <div>
                <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Root Cause Description</span>
                <p class="text-xs text-gray-800 bg-gray-50 border border-gray-100 p-3 rounded-lg mt-1 leading-relaxed">
                    {{ $finding->root_cause_description }}
                </p>
            </div>

            <div>
                <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Corrective Actions Executed</span>
                <p class="text-xs text-emerald-950 bg-emerald-50/50 border border-emerald-100 p-3 rounded-lg mt-1 leading-relaxed">
                    {{ $finding->corrective_action }}
                </p>
            </div>
        </div>
    </div>
@endif
