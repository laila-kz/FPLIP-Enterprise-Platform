<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('investigations', function (Blueprint $table) {
            $table->id();

            // Plain string, deliberately NOT a foreign key. Machine identity
            // belongs to the Gold layer / FastAPI, not to this database.
            $table->string('machine_id')->index();

            $table->enum('signal_type', ['oee_drop', 'scrap_spike', 'downtime_spike']);
            $table->enum('severity', ['high', 'medium', 'low']);
            $table->enum('status', ['open', 'assigned', 'pending_review', 'closed'])
                ->default('open')
                ->index();

            // The performance/loss/ML/AI context exactly as it looked at
            // open time — never re-fetched or overwritten afterward, so a
            // week-old investigation's evidence stays stable even as Gold
            // refreshes underneath it.
            $table->json('evidence_snapshot')->nullable();

            $table->foreignId('opened_by_id')
                ->constrained('users')
                ->restrictOnDelete();

            $table->foreignId('assigned_to_id')
                ->nullable()
                ->constrained('users')
                ->restrictOnDelete();

            $table->timestamp('opened_at');
            $table->timestamp('assigned_at')->nullable();
            $table->timestamp('closed_at')->nullable();

            $table->timestamps();

            $table->index('assigned_to_id');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('investigations');
    }
};
