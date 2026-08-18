@props([
    'title',
    'value',
    'change' => null,
    'changeType' => 'neutral', // 'positive', 'negative', 'warning', 'neutral'
    'subtitle' => null,
    'icon' => null,
    'accent' => 'blue' // 'blue', 'red', 'amber', 'emerald', 'indigo'
])

@php
    $accentBorder = match($accent) {
        'red' => 'border-l-red-500',
        'amber' => 'border-l-amber-500',
        'emerald' => 'border-l-emerald-500',
        'indigo' => 'border-l-indigo-500',
        default => 'border-l-blue-500'
    };
    $accentBg = match($accent) {
        'red' => 'bg-red-50 text-red-600',
        'amber' => 'bg-amber-50 text-amber-600',
        'emerald' => 'bg-emerald-50 text-emerald-600',
        'indigo' => 'bg-indigo-50 text-indigo-600',
        default => 'bg-blue-50 text-blue-600'
    };
@endphp

<div class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 border-l-4 {{ $accentBorder }} transition hover:shadow-md">
    <div class="flex items-center justify-between">
        <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ $title }}</span>
        @if($icon)
            <div class="w-8 h-8 rounded-lg {{ $accentBg }} flex items-center justify-center">
                {!! $icon !!}
            </div>
        @endif
    </div>
    <div class="mt-2 flex items-baseline justify-between">
        <div class="text-2xl font-bold text-gray-900 font-sans tracking-tight">{{ $value }}</div>
        @if($change)
            <span class="text-xs font-medium px-2 py-0.5 rounded-full {{ $changeType === 'positive' ? 'bg-emerald-50 text-emerald-700' : ($changeType === 'negative' ? 'bg-red-50 text-red-700' : 'bg-gray-100 text-gray-600') }}">
                {{ $change }}
            </span>
        @endif
    </div>
    @if($subtitle)
        <p class="text-xs text-gray-400 mt-1">{{ $subtitle }}</p>
    @endif
</div>
