@props(['signal'])

@php
    $sev = strtolower($signal['severity'] ?? 'medium');
    $detected = floatval($signal['detected_metric_value'] ?? 0);
    $baseline = floatval($signal['baseline_value'] ?? 0);
    $detectedPct = number_format($detected * 100, 1);
    $baselinePct = number_format($baseline * 100, 1);
    
    $borderClass = match($sev) {
        'high' => 'border-l-red-500 hover:border-red-600',
        'medium' => 'border-l-amber-500 hover:border-amber-600',
        default => 'border-l-blue-400 hover:border-blue-500'
    };
    
    $badgeClass = match($sev) {
        'high' => 'bg-red-50 text-red-700 border border-red-200',
        'medium' => 'bg-amber-50 text-amber-700 border border-amber-200',
        default => 'bg-blue-50 text-blue-700 border border-blue-200'
    };
@endphp

<div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 border-l-4 {{ $borderClass }} transition duration-200 hover:shadow-md flex flex-col justify-between">
    <div>
        <!-- Card Header -->
        <div class="flex items-start justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center font-mono font-bold text-slate-700 text-sm">
                    {{ str_replace('MACHINE-', 'M', $signal['machine_id']) }}
                </div>
                <div>
                    <h3 class="text-base font-bold text-gray-900 leading-tight">
                        {{ $signal['machine_id'] }}
                    </h3>
                    <span class="text-xs text-gray-400 font-mono">
                        {{ strtoupper(str_replace('_', ' ', $signal['signal_type'])) }}
                    </span>
                </div>
            </div>
            <span class="px-2.5 py-0.5 text-xs font-semibold rounded-full uppercase tracking-wider {{ $badgeClass }}">
                {{ $signal['severity'] }}
            </span>
        </div>

        <!-- Anomaly Headline -->
        <p class="mt-4 text-sm font-medium text-gray-800 leading-snug">
            {{ $signal['headline'] }}
        </p>

        <!-- Metric Delta Comparison Bar -->
        <div class="mt-4 bg-slate-50 border border-slate-100 rounded-lg p-3">
            <div class="flex justify-between items-center text-xs text-gray-600 mb-1.5">
                <span>Detected: <strong class="font-mono text-gray-900">{{ $detectedPct }}%</strong></span>
                <span class="text-gray-400 font-mono">Baseline: {{ $baselinePct }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden flex">
                <div class="h-2 rounded-full {{ $sev === 'high' ? 'bg-red-500' : ($sev === 'medium' ? 'bg-amber-500' : 'bg-blue-500') }}" style="width: {{ min(100, max(5, $detected * 100)) }}%"></div>
            </div>
        </div>
    </div>

    <!-- Actions Footer -->
    <div class="mt-5 pt-4 border-t border-gray-100 flex justify-end">
        <form method="POST" action="{{ route('investigations.open') }}">
            @csrf
            <input type="hidden" name="machine_id" value="{{ $signal['machine_id'] }}">
            <input type="hidden" name="signal_type" value="{{ $signal['signal_type'] }}">
            <input type="hidden" name="severity" value="{{ $signal['severity'] }}">
            <button type="submit" class="inline-flex items-center text-xs font-bold text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-3 py-1.5 rounded-lg transition active:scale-95 cursor-pointer">
                <span>Open Investigation</span>
                <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
            </button>
        </form>
    </div>
</div>
