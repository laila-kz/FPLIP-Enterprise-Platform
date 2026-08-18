@extends('layouts.app')

@section('title', 'Plant Anomaly Intelligence')

@section('content')
<div class="space-y-8">
    <!-- Top Dashboard Header & Telemetry Status -->
    <div class="flex flex-col sm:flex-row justify-between sm:items-center gap-4 pb-2">
        <div>
            <h1 class="text-2xl font-black text-slate-900 tracking-tight">Plant Signal Intelligence</h1>
            <p class="text-xs text-slate-500 mt-1 font-medium">Real-time Gold telemetry layer anomaly stream and automated scrap risk detection</p>
        </div>
        <div class="flex items-center space-x-3">
            <span class="inline-flex items-center px-3 py-1 rounded-lg text-xs font-mono font-semibold bg-white border border-slate-200 text-slate-700 shadow-2xs">
                <span class="w-2 h-2 rounded-full bg-emerald-500 mr-2"></span>
                BigQuery Gold Layer: Sync OK
            </span>
        </div>
    </div>

    <!-- Executive KPI Metric Summary Bar -->
    @php
        $signalCount = count($signals ?? []);
        $highSeverityCount = collect($signals ?? [])->where('severity', 'high')->count();
        $openCount = \App\Models\Investigation::where('status', '!=', 'closed')->count();
    @endphp

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <x-kpi-stat 
            title="Active Signals" 
            :value="$signalCount" 
            :change="$signalCount > 0 ? 'Live Anomaly' : 'Normal'" 
            :changeType="$signalCount > 0 ? 'warning' : 'positive'"
            subtitle="Real-time threshold breaches"
            accent="blue"
            icon='<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>'
        />

        <x-kpi-stat 
            title="Critical Severity" 
            :value="$highSeverityCount" 
            :change="$highSeverityCount > 0 ? 'Requires Action' : 'All Clear'" 
            :changeType="$highSeverityCount > 0 ? 'negative' : 'positive'"
            subtitle="Immediate technician dispatch"
            accent="red"
            icon='<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>'
        />

        <x-kpi-stat 
            title="Active Investigations" 
            :value="$openCount" 
            subtitle="Open or in-progress work orders"
            accent="amber"
            icon='<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>'
        />

        <x-kpi-stat 
            title="Plant Avg OEE" 
            value="75.2%" 
            change="+1.4%" 
            changeType="positive"
            subtitle="Target baseline 85.0%"
            accent="emerald"
            icon='<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>'
        />
    </div>

    @if (isset($plantContext) && $plantContext)
        <!-- Plant Multi-Function Telemetry & Physics Analyzer -->
        <x-telemetry-chart :context="$plantContext" machineId="LINE 1 • PLANT TELEMETRY STREAM" />
    @endif

    <!-- Anomaly Signal Stream -->
    <div>
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-lg font-bold text-slate-900 tracking-tight">Active Plant Signals</h2>
            <span class="text-xs font-mono text-slate-400">Stream refreshed automatically</span>
        </div>

        @if (empty($signals))
            <div class="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-12 text-center">
                <div class="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-3">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                </div>
                <p class="text-slate-800 text-base font-bold">No active signals detected</p>
                <p class="text-xs text-slate-400 mt-1">All production lines and machines are operating within baseline control tolerances.</p>
            </div>
        @else
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                @foreach ($signals as $signal)
                    <x-signal-card :signal="$signal" />
                @endforeach
            </div>
        @endif
    </div>
</div>
@endsection
