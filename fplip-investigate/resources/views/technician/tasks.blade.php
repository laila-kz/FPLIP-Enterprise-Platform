@extends('layouts.app')

@section('title', 'My Assigned Work Orders')

@section('content')
<div class="space-y-6">
    <!-- Tasks Header -->
    <div class="flex flex-col sm:flex-row justify-between sm:items-center gap-4 pb-2">
        <div>
            <h1 class="text-2xl font-black text-slate-900 tracking-tight">Technician Work Orders</h1>
            <p class="text-xs text-slate-500 mt-1 font-medium">Active root cause investigations and maintenance tasks assigned to your queue</p>
        </div>
        <div class="flex items-center space-x-3">
            <span class="inline-flex items-center px-3 py-1 rounded-lg text-xs font-mono font-semibold bg-white border border-slate-200 text-slate-700 shadow-2xs">
                <span class="w-2 h-2 rounded-full bg-blue-500 mr-2"></span>
                {{ $investigations->count() }} Assigned Task(s)
            </span>
        </div>
    </div>

    @if($investigations->isEmpty())
        <div class="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-12 text-center">
            <div class="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-3">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            </div>
            <p class="text-slate-800 text-base font-bold">You are all caught up!</p>
            <p class="text-xs text-slate-400 mt-1">No pending investigations are assigned to you at this moment.</p>
        </div>
    @else
        <div class="space-y-3.5">
            @foreach($investigations as $inv)
                @php
                    $sev = strtolower($inv->severity ?? 'medium');
                    $borderClass = match($sev) {
                        'high' => 'border-l-red-500',
                        'medium' => 'border-l-amber-500',
                        default => 'border-l-blue-400'
                    };
                    $badgeClass = match($sev) {
                        'high' => 'bg-red-50 text-red-700 border-red-200',
                        'medium' => 'bg-amber-50 text-amber-700 border-amber-200',
                        default => 'bg-blue-50 text-blue-700 border-blue-200'
                    };
                    $statusBadge = match($inv->status) {
                        'closed' => 'bg-emerald-50 text-emerald-700 border-emerald-200',
                        'pending_review' => 'bg-purple-50 text-purple-700 border-purple-200',
                        default => 'bg-blue-50 text-blue-700 border-blue-200'
                    };
                @endphp
                <div class="bg-white rounded-xl shadow-xs border border-slate-200/90 p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-l-4 {{ $borderClass }} hover:shadow-md transition">
                    <div class="flex items-start space-x-3.5">
                        <div class="w-11 h-11 rounded-lg bg-slate-100 flex items-center justify-center font-mono font-bold text-slate-700 text-sm">
                            {{ str_replace('MACHINE-', 'M', $inv->machine_id) }}
                        </div>
                        <div>
                            <div class="flex items-center space-x-2">
                                <a href="{{ route('investigations.show', $inv) }}" class="text-base font-bold text-slate-900 hover:text-blue-600 transition">
                                    Machine {{ $inv->machine_id }}
                                </a>
                                <span class="px-2 py-0.5 text-[10px] font-bold rounded-full uppercase tracking-wider border {{ $statusBadge }}">
                                    {{ str_replace('_', ' ', $inv->status) }}
                                </span>
                            </div>
                            <p class="text-xs text-slate-500 font-mono mt-0.5">
                                Anomaly: <strong class="text-slate-800">{{ strtoupper(str_replace('_', ' ', $inv->signal_type)) }}</strong> • 
                                Opened: {{ $inv->opened_at->diffForHumans() }}
                            </p>
                        </div>
                    </div>

                    <div class="flex items-center space-x-3 w-full md:w-auto justify-end">
                        <span class="px-2.5 py-0.5 text-xs font-semibold rounded-full uppercase tracking-wider border {{ $badgeClass }}">
                            {{ $inv->severity }}
                        </span>
                        <a href="{{ route('investigations.show', $inv) }}" class="inline-flex items-center text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg shadow-2xs transition active:scale-95">
                            <span>Open Workbench</span>
                            <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
                        </a>
                    </div>
                </div>
            @endforeach
        </div>
    @endif
</div>
@endsection
