<?php

namespace Database\Seeders;

use App\Models\Investigation;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class DatabaseSeeder extends Seeder
{
    /**
     * Deliberately builds sample investigations by calling the SAME
     * lifecycle methods (openFor / assignTo / recordFinding / close) the
     * real application uses — not raw ->create() calls on Investigation
     * with a hand-set status. This guarantees seeded data has a real,
     * consistent audit trail, exactly like data produced by an actual
     * user walking the UI, rather than a shortcut that could silently
     * drift from what the lifecycle methods actually enforce.
     */
    public function run(): void
    {
        $manager = User::firstOrCreate(
            ['email' => 'manager@fplip.test'],
            [
                'name' => 'Marcus Vance',
                'password' => Hash::make('password'),
                'role' => 'manager',
                'email_verified_at' => now(),
            ]
        );
        $manager->update([
            'name' => 'Marcus Vance',
            'password' => Hash::make('password'),
            'role' => 'manager',
            'email_verified_at' => now(),
        ]);

        $technicianOne = User::firstOrCreate(
            ['email' => 'technician1@fplip.test'],
            [
                'name' => 'David Miller',
                'password' => Hash::make('password'),
                'role' => 'technician',
                'email_verified_at' => now(),
            ]
        );
        $technicianOne->update([
            'name' => 'David Miller',
            'password' => Hash::make('password'),
            'role' => 'technician',
            'email_verified_at' => now(),
        ]);

        $technicianTwo = User::firstOrCreate(
            ['email' => 'technician2@fplip.test'],
            [
                'name' => 'Elena Kim',
                'password' => Hash::make('password'),
                'role' => 'technician',
                'email_verified_at' => now(),
            ]
        );
        $technicianTwo->update([
            'name' => 'Elena Kim',
            'password' => Hash::make('password'),
            'role' => 'technician',
            'email_verified_at' => now(),
        ]);

        // --- Investigation #1: open, unassigned ---
        // Represents a Manager who opened a signal but hasn't assigned it yet.
        Investigation::openFor(
            machineId: 'M003',
            signalType: 'oee_drop',
            severity: 'high',
            evidenceSnapshot: [
                'performance' => ['oee' => 0.642, 'availability' => 0.71, 'performance' => 0.95, 'quality' => 0.952],
                'loss_attribution' => [
                    'availability_loss_sec' => 5100,
                    'performance_loss_sec' => 400,
                    'unmapped_loss_sec' => 100,
                ],
                'scrap' => ['top_defect_category' => 'Dimensional Out-of-Spec', 'rejected_units' => 11],
            ],
            openedBy: $manager,
        );

        // --- Investigation #2: open, then assigned ---
        $investigationTwo = Investigation::openFor(
            machineId: 'M005',
            signalType: 'scrap_spike',
            severity: 'medium',
            evidenceSnapshot: [
                'performance' => ['oee' => 0.781, 'availability' => 0.88, 'performance' => 0.97, 'quality' => 0.91],
                'loss_attribution' => [
                    'availability_loss_sec' => 1800,
                    'performance_loss_sec' => 300,
                    'unmapped_loss_sec' => 50,
                ],
                'scrap' => ['top_defect_category' => 'Surface Finish Defect', 'rejected_units' => 7],
            ],
            openedBy: $manager,
        );
        $investigationTwo->assignTo($technicianOne, $manager);

        // --- Investigation #3: full lifecycle, closed ---
        $investigationThree = Investigation::openFor(
            machineId: 'M002',
            signalType: 'downtime_spike',
            severity: 'low',
            evidenceSnapshot: [
                'performance' => ['oee' => 0.812, 'availability' => 0.90, 'performance' => 0.96, 'quality' => 0.94],
                'loss_attribution' => [
                    'availability_loss_sec' => 900,
                    'performance_loss_sec' => 150,
                    'unmapped_loss_sec' => 25,
                ],
                'scrap' => ['top_defect_category' => 'N/A', 'rejected_units' => 0],
            ],
            openedBy: $manager,
        );
        $investigationThree->assignTo($technicianTwo, $manager);
        $investigationThree->recordFinding(
            [
                'root_cause_category' => 'Changeover Delay',
                'corrective_action' => 'Retrained shift lead on quick-changeover checklist; posted revised SOP at the station.',
                'notes' => 'Downtime traced to an extended tooling changeover during shift handoff. No mechanical fault found.',
            ],
            $technicianTwo,
        );
        $investigationThree->close($manager);

        $this->command->info('Seeded: 1 manager, 2 technicians, 3 investigations (open / assigned / closed).');
    }
}
