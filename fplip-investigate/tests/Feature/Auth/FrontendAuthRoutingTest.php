<?php

namespace Tests\Feature\Auth;

use App\Models\Investigation;
use App\Models\User;
use Database\Seeders\DatabaseSeeder;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Hash;
use Tests\TestCase;

class FrontendAuthRoutingTest extends TestCase
{
    use RefreshDatabase;

    public function test_demo_accounts_are_seeded_idempotently_with_expected_roles(): void
    {
        $this->seed(DatabaseSeeder::class);
        $this->seed(DatabaseSeeder::class);

        $this->assertDatabaseHas('users', [
            'email' => 'manager@fplip.test',
            'role' => 'manager',
        ]);

        $this->assertDatabaseHas('users', [
            'email' => 'technician1@fplip.test',
            'role' => 'technician',
        ]);

        $manager = User::where('email', 'manager@fplip.test')->firstOrFail();
        $this->assertTrue(Hash::check('password', $manager->password));
    }

    public function test_manager_detail_route_exists_for_manager_prefix(): void
    {
        $this->seed(DatabaseSeeder::class);
        $manager = User::where('email', 'manager@fplip.test')->firstOrFail();

        $investigation = Investigation::openFor(
            machineId: 'M003',
            signalType: 'oee_drop',
            severity: 'high',
            evidenceSnapshot: ['ok' => true],
            openedBy: $manager,
        );

        $response = $this->actingAs($manager)->get('/manager/investigations/' . $investigation->id);

        $response->assertStatus(200);
    }

    public function test_dashboard_falls_back_when_fastapi_is_unreachable(): void
    {
        config()->set('fastapi.base_url', 'http://127.0.0.1:65535');

        $manager = User::factory()->create([
            'role' => 'manager',
            'email' => 'manager@fplip.test',
        ]);

        $response = $this->actingAs($manager)->get('/manager/dashboard');

        $response->assertOk();
        $response->assertSee('OEE dropped 15% below baseline');
    }
}
