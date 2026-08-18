<!DOCTYPE html>
<html lang="en" class="h-full bg-slate-50">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>@yield('title', 'FPLIP Investigate') - Manufacturing Root Cause Suite</title>
    
    <!-- Modern Sans & Monospace Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Local Production Assets via Vite -->
    @vite(['resources/css/app.css', 'resources/js/app.js'])
    <style>
        body { font-family: 'Inter', system-ui, sans-serif; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
    </style>
</head>
<body class="h-full bg-slate-50 text-slate-800 antialiased flex flex-col min-h-screen">
    <!-- Top Ecosystem Header Bar -->
    <header class="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-16">
                <!-- Left: Branding & Plant Status -->
                <div class="flex items-center space-x-6">
                    <a href="{{ auth()->check() ? (auth()->user()->role === 'manager' ? route('investigations.dashboard') : route('technician.tasks')) : '/' }}" class="flex items-center space-x-2.5 group">
                        <div class="w-9 h-9 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-lg shadow-sm group-hover:bg-blue-700 transition">
                            ⚡
                        </div>
                        <div>
                            <span class="text-base font-extrabold text-slate-900 tracking-tight leading-none block">FPLIP <span class="text-blue-600 font-bold">Investigate</span></span>
                            <span class="text-[10px] text-slate-400 font-mono tracking-wider uppercase block">Industrial Root Cause Suite</span>
                        </div>
                    </a>

                    <!-- Plant Telemetry Live Pill -->
                    <div class="hidden md:flex items-center space-x-2 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full">
                        <span class="relative flex h-2 w-2">
                            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                            <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                        </span>
                        <span class="text-xs font-semibold text-emerald-800">Plant Live</span>
                        <span class="text-[10px] text-emerald-600 font-mono">Port 8080</span>
                    </div>
                </div>

                <!-- Center: Navigation Links -->
                @auth
                    <nav class="hidden sm:flex items-center space-x-1">
                        @if(Auth::user()->role === 'manager')
                            <a href="{{ route('investigations.dashboard') }}" class="px-3.5 py-2 text-xs font-bold rounded-lg transition {{ request()->routeIs('investigations.dashboard') ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100' }}">
                                Signals Dashboard
                            </a>
                        @endif

                        <a href="{{ route('technician.tasks') }}" class="px-3.5 py-2 text-xs font-bold rounded-lg transition {{ request()->routeIs('technician.tasks') ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100' }}">
                            Technician Work Orders
                        </a>
                    </nav>
                @endauth

                <!-- Right: Persona Quick-Switcher & User Profile -->
                <div class="flex items-center space-x-3">
                    @auth
                        <!-- Persona Quick-Switch Dropdown for fast testing -->
                        <div class="hidden lg:flex items-center space-x-1 bg-slate-100 p-1 rounded-lg border border-slate-200">
                            <span class="text-[10px] uppercase font-bold text-slate-400 px-1.5 font-mono">Demo:</span>
                            <a href="{{ route('switch.role', 'manager') }}" class="px-2 py-0.5 text-xs font-semibold rounded {{ Auth::user()->role === 'manager' ? 'bg-white shadow-xs text-blue-700 font-bold' : 'text-slate-600 hover:text-slate-900' }}">
                                Manager
                            </a>
                            <a href="{{ route('switch.role', 'technician') }}" class="px-2 py-0.5 text-xs font-semibold rounded {{ Auth::user()->role === 'technician' ? 'bg-white shadow-xs text-blue-700 font-bold' : 'text-slate-600 hover:text-slate-900' }}">
                                Tech
                            </a>
                        </div>

                        <!-- Current User Info -->
                        <div class="flex items-center space-x-2.5 pl-2 border-l border-slate-200">
                            <div class="text-right hidden sm:block">
                                <div class="text-xs font-bold text-slate-900 leading-tight">{{ Auth::user()->name }}</div>
                                <span class="text-[10px] font-mono uppercase px-1.5 py-0.2 rounded-full font-bold {{ Auth::user()->role === 'manager' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800' }}">
                                    {{ Auth::user()->role }}
                                </span>
                            </div>

                            <form method="POST" action="{{ route('logout') }}" class="inline">
                                @csrf
                                <button type="submit" class="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition" title="Log Out">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
                                </button>
                            </form>
                        </div>
                    @else
                        <a href="{{ route('login') }}" class="text-xs font-bold text-blue-600 hover:text-blue-800 px-3 py-1.5 rounded-lg border border-blue-200 hover:bg-blue-50 transition">
                            Sign In
                        </a>
                    @endauth
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <!-- Flash Messages -->
        @if (session('success'))
            <div class="mb-6 bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-3.5 rounded-xl shadow-xs flex items-center justify-between">
                <div class="flex items-center space-x-2.5">
                    <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                    <span class="text-sm font-semibold">{{ session('success') }}</span>
                </div>
            </div>
        @endif

        @if ($errors->any())
            <div class="mb-6 bg-red-50 border border-red-200 text-red-800 px-4 py-3.5 rounded-xl shadow-xs">
                <div class="flex items-center space-x-2.5 mb-1.5">
                    <svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                    <span class="text-sm font-bold">Please check the following errors:</span>
                </div>
                <ul class="list-disc list-inside text-xs space-y-0.5 ml-7 text-red-700">
                    @foreach ($errors->all() as $error)
                        <li>{{ $error }}</li>
                    @endforeach
                </ul>
            </div>
        @endif

        @yield('content')
    </main>

    <!-- Unified Ecosystem Footer -->
    <footer class="bg-white border-t border-slate-200 py-4 mt-auto">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row justify-between items-center text-xs text-slate-400">
            <div class="flex items-center space-x-3 mb-2 sm:mb-0">
                <span class="font-bold text-slate-600">FPLIP Manufacturing Intelligence</span>
                <span>•</span>
                <span class="font-mono">FastAPI 8080</span>
                <span>•</span>
                <span class="font-mono">Laravel 8081</span>
                <span>•</span>
                <span class="font-mono">Gemini 3.5 Flash Lite</span>
            </div>
            <div class="font-mono text-[11px]">
                Active Session: {{ Auth::user()->email ?? 'Guest' }}
            </div>
        </div>
    </footer>
</body>
</html>
