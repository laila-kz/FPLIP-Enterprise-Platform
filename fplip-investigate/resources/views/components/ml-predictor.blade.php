@props(['mlRisk'])

@if($mlRisk)
    @php
        $prob = floatval($mlRisk['probability'] ?? 0);
        $probPct = number_format($prob * 100, 1);
        $band = strtolower($mlRisk['risk_band'] ?? 'low');
        $threshold = floatval($mlRisk['risk_threshold'] ?? 0.594);
        
        $badgeClass = match($band) {
            'high' => 'bg-red-100 text-red-800 border-red-200',
            'elevated', 'medium' => 'bg-amber-100 text-amber-800 border-amber-200',
            default => 'bg-emerald-100 text-emerald-800 border-emerald-200'
        };
        
        $meterColor = match($band) {
            'high' => 'bg-red-500',
            'elevated', 'medium' => 'bg-amber-500',
            default => 'bg-emerald-500'
        };
    @endphp

    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
            <div class="flex items-center space-x-2">
                <svg class="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                <h3 class="text-base font-bold text-gray-900">ML Scrap Risk Predictor</h3>
            </div>
            <span class="text-xs font-mono bg-indigo-50 text-indigo-700 font-semibold px-2.5 py-1 rounded-md">Scikit-Learn 1.9</span>
        </div>

        <!-- Risk Probability Gauge -->
        <div class="bg-slate-50 border border-slate-100 rounded-xl p-4">
            <div class="flex justify-between items-center mb-2">
                <div>
                    <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Estimated Scrap Risk</span>
                    <div class="text-3xl font-black text-gray-900 font-sans mt-0.5">{{ $probPct }}%</div>
                </div>
                <div class="text-right">
                    <span class="px-3 py-1 text-xs font-bold rounded-full uppercase tracking-wider border {{ $badgeClass }}">
                        {{ strtoupper($mlRisk['risk_band']) }} RISK
                    </span>
                    <div class="text-xs text-gray-400 font-mono mt-1.5">Threshold: {{ number_format($threshold * 100, 1) }}%</div>
                </div>
            </div>

            <div class="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden flex mt-3">
                <div class="{{ $meterColor }} h-2.5 rounded-full transition-all duration-500" style="width: {{ min(100, max(5, $prob * 100)) }}%"></div>
            </div>
        </div>

        <!-- Top Factor Drivers -->
        @if(isset($mlRisk['top_factors']) && count($mlRisk['top_factors']) > 0)
            <div>
                <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2.5">Key Model Drivers (Pre-Run Telemetry)</h4>
                <div class="space-y-2">
                    @foreach($mlRisk['top_factors'] as $factor)
                        @php
                            $isInc = ($factor['direction'] ?? '') === 'increases';
                        @endphp
                        <div class="flex justify-between items-center text-xs p-2.5 rounded-lg border {{ $isInc ? 'bg-red-50/50 border-red-100 text-red-900' : 'bg-emerald-50/50 border-emerald-100 text-emerald-900' }}">
                            <span class="font-mono font-medium">{{ str_replace('_', ' ', $factor['feature']) }}</span>
                            <span class="font-semibold flex items-center">
                                @if($isInc)
                                    <span class="mr-1 text-red-600">▲ Increases Risk</span>
                                @else
                                    <span class="mr-1 text-emerald-600">▼ Decreases Risk</span>
                                @endif
                                <span class="font-mono text-gray-700">({{ number_format($factor['impact'], 2) }})</span>
                            </span>
                        </div>
                    @endforeach
                </div>
            </div>
        @endif
    </div>
@endif
