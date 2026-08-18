<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

// Adds `role` to Laravel's default `users` table rather than redefining
// the whole table — this migration is meant to run after Breeze's own
// create_users_table migration. If you're starting from a completely
// fresh install, this file assumes that default migration already exists.
return new class extends Migration
{
    public function up(): void
    {
        Schema::table('users', function (Blueprint $table) {
            $table->enum('role', ['manager', 'technician'])
                ->default('technician')
                ->after('email');
        });
    }

    public function down(): void
    {
        Schema::table('users', function (Blueprint $table) {
            $table->dropColumn('role');
        });
    }
};
