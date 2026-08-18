<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}" class="h-full bg-slate-50">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="csrf-token" content="{{ csrf_token() }}">

        <title>{{ config('app.name', 'FPLIP Investigate') }} - Sign In</title>

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
    <body class="h-full bg-slate-50 text-slate-800 antialiased flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div class="sm:mx-auto sm:w-full sm:max-w-md text-center">
            <div class="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-blue-600 text-white font-black text-2xl shadow-sm mb-3">
                ⚡
            </div>
            <h2 class="text-2xl font-black text-slate-900 tracking-tight">FPLIP <span class="text-blue-600 font-bold">Investigate</span></h2>
            <p class="text-xs text-slate-500 font-medium mt-1">Manufacturing Root Cause & Anomaly Intelligence</p>
        </div>

        <div class="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
            <div class="bg-white py-8 px-6 shadow-sm border border-slate-200 rounded-2xl sm:px-10">
                {{ $slot }}
            </div>

            <!-- Demo Quick Login Helper -->
            <div class="mt-6 bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
                <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2 text-center font-mono">1-Click Test Demo Logins</span>
                <div class="grid grid-cols-2 gap-2">
                    <button type="button" onclick="fillDemo('manager@fplip.test', 'password')" class="text-xs font-bold text-purple-700 bg-purple-50 hover:bg-purple-100 border border-purple-200 py-2 px-3 rounded-lg transition text-center cursor-pointer">
                        Manager (Sarah)
                    </button>
                    <button type="button" onclick="fillDemo('technician1@fplip.test', 'password')" class="text-xs font-bold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 py-2 px-3 rounded-lg transition text-center cursor-pointer">
                        Tech (David)
                    </button>
                </div>
            </div>
        </div>

        <script>
        function fillDemo(email, pass) {
            const emailInput = document.getElementById('email');
            const passInput = document.getElementById('password');
            if (emailInput) emailInput.value = email;
            if (passInput) passInput.value = pass;
        }
        </script>
    </body>
</html>
