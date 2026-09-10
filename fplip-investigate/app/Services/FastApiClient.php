<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use App\Exceptions\FastApiException;

class FastApiClient
{
    protected string $baseUrl;
    protected ?string $apiKey;
    protected int $timeout;

    public function __construct()
    {
        $this->baseUrl = config('fastapi.base_url');
        $this->apiKey = config('fastapi.api_key');
        $this->timeout = config('fastapi.timeout', 90);
    }

    public function health(): array
    {
        // No API key required for health check
        $response = Http::timeout($this->timeout)
            ->withHeaders([
                'Accept' => 'application/json',
            ])
            ->get($this->baseUrl . '/health');

        if ($response->failed()) {
            throw new FastApiException(
                'FastAPI health check failed: ' . $response->status() . ' - ' . $response->body()
            );
        }

        return $response->json();
    }

    // Other methods will include the API key
    public function activeSignals(): array
    {
        $response = Http::timeout($this->timeout)
            ->withHeaders([
                'X-Internal-Key' => $this->apiKey,
                'X-API-Key' => $this->apiKey,
                'Accept' => 'application/json',
            ])
            ->get($this->baseUrl . '/signals/active');

        if ($response->failed()) {
            throw new FastApiException('FastAPI active signals failed: ' . $response->status());
        }

        return $response->json();
    }

    /**
     * Get machine context (performance, loss, scrap) for a date range.
     */
    public function machineContext(string $machineId, string $startDate, string $endDate): array
    {
        $response = Http::timeout($this->timeout)
            ->withHeaders([
                'X-Internal-Key' => $this->apiKey,
                'X-API-Key' => $this->apiKey,
                'Accept' => 'application/json',
            ])
            ->get($this->baseUrl . '/machine/context', [
                'machine_id' => $machineId,
                'start_date' => $startDate,
                'end_date' => $endDate,
            ]);

        if ($response->failed()) {
            throw new FastApiException('FastAPI machine context failed: ' . $response->status());
        }

        return $response->json();
    }

    /**
     * Get scrap risk prediction using ML model.
     */
    public function scrapRisk(string $machineId, string $productId, string $shiftId, int $plannedUnits): array
    {
        $response = Http::timeout($this->timeout)
            ->withHeaders([
                'X-Internal-Key' => $this->apiKey,
                'X-API-Key' => $this->apiKey,
                'Accept' => 'application/json',
            ])
            ->post($this->baseUrl . '/ml/scrap-risk', [
                'machine_id' => $machineId,
                'product_id' => $productId,
                'shift_id' => $shiftId,
                'planned_units' => $plannedUnits,
            ]);

        if ($response->failed()) {
            throw new FastApiException('Scrap risk prediction failed: ' . $response->status());
        }

        return $response->json();
    }

    /**
     * Generate Gemini AI operational explanation for an investigation.
     */
    public function explain(string $machineId, string $signalType, string $severity, ?array $context = null, ?array $mlRisk = null): array
    {
        $response = Http::timeout($this->timeout)
            ->withHeaders([
                'X-Internal-Key' => $this->apiKey,
                'X-API-Key' => $this->apiKey,
                'Accept' => 'application/json',
            ])
            ->post($this->baseUrl . '/ai/explain', [
                'machine_id' => $machineId,
                'signal_type' => $signalType,
                'severity' => $severity,
                'context' => $context,
                'ml_risk' => $mlRisk,
            ]);

        if ($response->failed()) {
            throw new FastApiException('AI explanation request failed: ' . $response->status());
        }

        return $response->json();
    }
}