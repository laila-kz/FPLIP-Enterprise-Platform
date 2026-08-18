@props(['investigation'])

<div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
    <div class="flex items-center justify-between pb-3 border-b border-gray-100">
        <div class="flex items-center space-x-2">
            <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            <h3 class="text-base font-bold text-gray-900">Investigation Lifecycle & Audit Trail</h3>
        </div>
        <span class="text-xs font-mono text-gray-400">{{ $investigation->auditLogs->count() }} logged events</span>
    </div>

    @if($investigation->auditLogs->isEmpty())
        <p class="text-xs text-gray-400 italic py-2">No audit events recorded.</p>
    @else
        <div class="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-gray-200">
            @foreach($investigation->auditLogs as $log)
                <div class="relative flex items-start space-x-3 text-xs">
                    <div class="absolute -left-6 mt-1 w-3 h-3 rounded-full bg-blue-600 border-2 border-white shadow-sm"></div>
                    <div class="flex-1 bg-slate-50 border border-slate-100 p-3 rounded-xl">
                        <div class="flex justify-between items-center mb-1">
                            <span class="font-bold text-gray-900 capitalize">
                                {{ str_replace('_', ' ', $log->action) }}
                            </span>
                            <span class="text-xs font-mono text-gray-400">
                                {{ $log->created_at->format('M d, H:i:s') }}
                            </span>
                        </div>
                        <div class="text-gray-600">
                            By <strong class="text-gray-800">{{ $log->user->name ?? 'System' }}</strong>
                            <span class="text-xs text-gray-400">({{ $log->user->role ?? 'automated' }})</span>
                        </div>
                        @if(!empty($log->details))
                            <div class="mt-2 text-xs font-mono bg-white p-2 rounded border border-gray-100 text-gray-700 overflow-x-auto">
                                @if(is_array($log->details))
                                    @foreach($log->details as $k => $v)
                                        <div><strong class="text-gray-500">{{ $k }}:</strong> {{ is_array($v) ? json_encode($v) : $v }}</div>
                                    @endforeach
                                @else
                                    {{ $log->details }}
                                @endif
                            </div>
                        @endif
                    </div>
                </div>
            @endforeach
        </div>
    @endif
</div>
