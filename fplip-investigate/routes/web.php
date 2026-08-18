<?php

use App\Http\Controllers\InvestigationController;
use App\Http\Controllers\TechnicianController;
use App\Http\Controllers\ProfileController;
use Illuminate\Support\Facades\Route;
use Illuminate\Support\Facades\Auth;

Route::get('/', function () {
    return redirect()->route('login');
});

// ===== Manager Routes =====
Route::middleware(['auth', 'role:manager'])->prefix('manager')->group(function () {
    Route::get('/dashboard', [InvestigationController::class, 'dashboard'])->name('investigations.dashboard');
    Route::get('/investigations/{investigation}', [InvestigationController::class, 'show'])->name('manager.investigations.show');
    Route::post('/investigations/open', [InvestigationController::class, 'open'])->name('investigations.open');
    Route::post('/investigations/{investigation}/assign', [InvestigationController::class, 'assign'])->name('investigations.assign');
    Route::post('/investigations/{investigation}/close', [InvestigationController::class, 'close'])->name('investigations.close');
});

// ===== Technician & Work Orders Routes =====
Route::middleware(['auth', 'role:technician,manager'])->prefix('technician')->group(function () {
    Route::get('/tasks', [TechnicianController::class, 'myTasks'])->name('technician.tasks');
    Route::post('/investigations/{investigation}/findings', [TechnicianController::class, 'submitFindings'])->name('technician.findings.submit');
});

// ===== Shared Routes (both roles) =====
Route::middleware('auth')->group(function () {
    Route::get('/investigations/{investigation}', [InvestigationController::class, 'show'])->name('investigations.show');
    Route::post('/investigations/{investigation}/explain', [InvestigationController::class, 'explain'])->name('investigations.explain');
    Route::get('/profile', [ProfileController::class, 'edit'])->name('profile.edit');
    Route::patch('/profile', [ProfileController::class, 'update'])->name('profile.update');
    Route::delete('/profile', [ProfileController::class, 'destroy'])->name('profile.destroy');
});

// ===== Dev Routes =====
Route::get('/dev/health-check', function (\App\Services\FastApiClient $client) {
    try {
        $result = $client->health();
        return response()->json([
            'status' => 'ok',
            'fastapi' => $result,
        ]);
    } catch (\App\Exceptions\FastApiException $e) {
        return response()->json([
            'status' => 'error',
            'message' => $e->getMessage(),
        ], 503);
    }
});

Route::get('/switch-role/{role}', function (string $role, \Illuminate\Http\Request $request) {
    $email = match($role) {
        'manager' => 'manager@fplip.test',
        'technician' => 'technician1@fplip.test',
        'operator' => 'operator@fplip.test',
        default => 'manager@fplip.test'
    };
    $user = \App\Models\User::where('email', $email)->first();
    if ($user) {
        Auth::login($user);
        $request->session()->regenerate();
    }
    if ($role === 'technician') {
        return redirect()->route('technician.tasks');
    }
    return redirect()->route('investigations.dashboard');
})->name('switch.role');

Route::get('/dev/users', function () {
    return App\Models\User::all()->map(function ($user) {
        return [
            'name' => $user->name,
            'email' => $user->email,
            'role' => $user->role,
        ];
    });
});

require __DIR__.'/auth.php';
