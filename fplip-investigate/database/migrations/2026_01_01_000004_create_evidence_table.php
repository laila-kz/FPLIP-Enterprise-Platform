<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('evidence', function (Blueprint $table) {
            $table->id();

            $table->foreignId('investigation_id')
                ->constrained('investigations')
                ->cascadeOnDelete();

            // Nullable: evidence can be attached at any point while an
            // investigation is open, not only when a finding is submitted.
            $table->foreignId('finding_id')
                ->nullable()
                ->constrained('findings')
                ->nullOnDelete();

            $table->foreignId('uploaded_by_id')
                ->constrained('users')
                ->restrictOnDelete();

            // Path into a PRIVATE disk only. Never store a public/ path
            // here — the file is served exclusively through an
            // authorization-checked controller route (see EvidencePolicy).
            $table->string('file_path');
            $table->string('file_name');
            $table->string('mime_type');
            $table->unsignedInteger('file_size_bytes');
            $table->text('note')->nullable();

            $table->timestamp('uploaded_at');

            $table->timestamps();

            $table->index('investigation_id');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('evidence');
    }
};
