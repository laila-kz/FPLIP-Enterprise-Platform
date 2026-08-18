@props(['context'])

<div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-6">
    <div class="flex items-center justify-between pb-3 border-b border-gray-100">
        <div class="flex items-center space-x-2">
            <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
            <h3 class="text-base font-bold text-gray-900">Telemetry & OEE Performance</h3>
        </div>
        <span class="text-xs font-mono bg-slate-100 text-slate-700 font-semibold px-2.5 py-1 rounded-md">Live Telemetry</span>
    </div>

    @if(isset($context['performance']))
        <!-- OEE Metric Gauges Grid -->
        <div class="grid grid-cols-2 gap-4">
            <div class="bg-slate-50 border border-slate-100 p-3.5 rounded-xl">
                <div class="flex justify-between items-center text-xs text-gray-500 font-medium">
                    <span>Overall OEE</span>
                    <span class="font-mono text-gray-400">Target 85%</span>
                </div>
                <div class="text-2xl font-black text-gray-900 mt-1 font-sans">
                    {{ number_format($context['performance']['oee'] * 100, 1) }}%
                </div>
                <div class="w-full bg-gray-200 rounded-full h-1.5 mt-2">
                    <div class="bg-amber-500 h-1.5 rounded-full" style="width: {{ $context['performance']['oee'] * 100 }}%"></div>
                </div>
            </div>

            <div class="bg-slate-50 border border-slate-100 p-3.5 rounded-xl">
                <div class="flex justify-between items-center text-xs text-gray-500 font-medium">
                    <span>Availability</span>
                    <span class="font-mono text-gray-400">Target 90%</span>
                </div>
                <div class="text-2xl font-black text-gray-900 mt-1 font-sans">
                    {{ number_format($context['performance']['availability'] * 100, 1) }}%
                </div>
                <div class="w-full bg-gray-200 rounded-full h-1.5 mt-2">
                    <div class="bg-amber-500 h-1.5 rounded-full" style="width: {{ $context['performance']['availability'] * 100 }}%"></div>
                </div>
            </div>

            <div class="bg-slate-50 border border-slate-100 p-3.5 rounded-xl">
                <div class="flex justify-between items-center text-xs text-gray-500 font-medium">
                    <span>Performance</span>
                    <span class="font-mono text-gray-400">Target 95%</span>
                </div>
                <div class="text-2xl font-black text-gray-900 mt-1 font-sans">
                    {{ number_format($context['performance']['performance'] * 100, 1) }}%
                </div>
                <div class="w-full bg-gray-200 rounded-full h-1.5 mt-2">
                    <div class="bg-emerald-500 h-1.5 rounded-full" style="width: {{ $context['performance']['performance'] * 100 }}%"></div>
                </div>
            </div>

            <div class="bg-slate-50 border border-slate-100 p-3.5 rounded-xl">
                <div class="flex justify-between items-center text-xs text-gray-500 font-medium">
                    <span>Quality</span>
                    <span class="font-mono text-gray-400">Target 99%</span>
                </div>
                <div class="text-2xl font-black text-gray-900 mt-1 font-sans">
                    {{ number_format($context['performance']['quality'] * 100, 1) }}%
                </div>
                <div class="w-full bg-gray-200 rounded-full h-1.5 mt-2">
                    <div class="bg-emerald-500 h-1.5 rounded-full" style="width: {{ $context['performance']['quality'] * 100 }}%"></div>
                </div>
            </div>
        </div>
    @endif

    <!-- Loss Attribution Breakdown -->
    @if(isset($context['loss_attribution']))
        @php
            $availLoss = $context['loss_attribution']['availability_loss_sec'] ?? 0;
            $perfLoss = $context['loss_attribution']['performance_loss_sec'] ?? 0;
            $unmappedLoss = $context['loss_attribution']['unmapped_loss_sec'] ?? 0;
            $totalLoss = max(1, $availLoss + $perfLoss + $unmappedLoss);
            $availPct = round(($availLoss / $totalLoss) * 100);
            $perfPct = round(($perfLoss / $totalLoss) * 100);
            $unmappedPct = round(($unmappedLoss / $totalLoss) * 100);
        @endphp
        <div class="border-t border-gray-100 pt-5">
            <div class="flex justify-between items-center mb-3">
                <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Loss Attribution Breakdown</h4>
                <span class="text-xs font-mono text-gray-400">Total: {{ number_format($totalLoss / 60, 1) }} min</span>
            </div>

            <div class="w-full bg-gray-100 h-3 rounded-full overflow-hidden flex mb-3.5 shadow-inner">
                <div class="bg-red-500 h-3 transition-all" style="width: {{ $availPct }}%" title="Availability Loss: {{ $availPct }}%"></div>
                <div class="bg-amber-500 h-3 transition-all" style="width: {{ $perfPct }}%" title="Performance Loss: {{ $perfPct }}%"></div>
                <div class="bg-slate-400 h-3 transition-all" style="width: {{ $unmappedPct }}%" title="Unmapped Loss: {{ $unmappedPct }}%"></div>
            </div>

            <div class="space-y-2 text-xs">
                <div class="flex justify-between items-center">
                    <span class="flex items-center text-gray-700">
                        <span class="w-2.5 h-2.5 rounded-full bg-red-500 inline-block mr-2"></span>
                        Availability Loss (Downtime/Stops)
                    </span>
                    <span class="font-mono font-semibold text-gray-900">{{ number_format($availLoss) }}s ({{ $availPct }}%)</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="flex items-center text-gray-700">
                        <span class="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block mr-2"></span>
                        Performance Loss (Speed/Cycle)
                    </span>
                    <span class="font-mono font-semibold text-gray-900">{{ number_format($perfLoss) }}s ({{ $perfPct }}%)</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="flex items-center text-gray-700">
                        <span class="w-2.5 h-2.5 rounded-full bg-slate-400 inline-block mr-2"></span>
                        Unmapped Operational Loss
                    </span>
                    <span class="font-mono font-semibold text-gray-900">{{ number_format($unmappedLoss) }}s ({{ $unmappedPct }}%)</span>
                </div>
            </div>
        </div>
    @endif

    <!-- Scrap & Defect Summary -->
    @if(isset($context['scrap']))
        <div class="border-t border-gray-100 pt-5">
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2.5">Scrap & Defect Classification</h4>
            <div class="bg-red-50/70 border border-red-100 rounded-xl p-3.5">
                <div class="text-xs font-medium text-red-600">Dominant Defect Category:</div>
                <div class="text-sm font-bold text-red-950 mt-0.5">{{ $context['scrap']['top_defect_category'] ?? 'N/A' }}</div>
                <div class="flex justify-between text-xs text-red-800 mt-2.5 pt-2 border-t border-red-200/50">
                    <span>Rejected Units: <strong class="font-mono">{{ $context['scrap']['rejected_units'] ?? 0 }}</strong></span>
                    @if(isset($context['scrap']['scrap_rate']))
                        <span>Scrap Rate: <strong class="font-mono">{{ number_format($context['scrap']['scrap_rate'] * 100, 2) }}%</strong></span>
                    @endif
                </div>
            </div>
        </div>
    @endif
</div>
