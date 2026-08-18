<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('findings', function (Blueprint $table) {
            $table->id();

            // unique() enforces "one finding per investigation" at the
            // database level, not just in application logic — a second
            // submission attempt will fail with a constraint violation
            // even if a controller-level check were ever bypassed.
            $table->foreignId('investigation_id')
                ->unique()
                ->constrained('investigations')
                ->cascadeOnDelete();

            $table->foreignId('technician_id')
                ->constrained('users')
                ->restrictOnDelete();

            // String, not a DB enum — validated against a config-defined
            // list (config/investigations.php) at the application layer,
            // so the category list can grow without a migration.
            $table->string('root_cause_category');

            $table->text('corrective_action');
            $table->text('notes')->nullable();

            $table->timestamp('submitted_at');

            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('findings');
    }
};
