<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('audit_logs', function (Blueprint $table) {
            $table->id();

            $table->foreignId('investigation_id')
                ->constrained('investigations')
                ->cascadeOnDelete();

            $table->foreignId('actor_id')
                ->constrained('users')
                ->restrictOnDelete();

            // e.g. 'opened', 'assigned', 'finding_submitted',
            // 'evidence_attached', 'closed'. A plain string, not a DB enum
            // — new event types can be added without a migration, since
            // this table exists purely to be read, never validated against.
            $table->string('event_type');

            $table->text('description')->nullable();
            $table->json('metadata')->nullable();

            // Append-only: created_at only, no updated_at. A row, once
            // written, is never modified — that's what makes this a real
            // audit trail rather than just a mutable status-history table.
            $table->timestamp('created_at')->useCurrent();

            $table->index('investigation_id');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('audit_logs');
    }
};
