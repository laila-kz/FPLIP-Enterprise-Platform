#!/usr/bin/env python3
"""
Measure API endpoint latency (cache-cold and cache-warm).
"""

import time
import httpx
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"

# Find a date range that has data (adjust these to match your actual data)
# First, check what dates exist
END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=7)

ENDPOINTS = [
    ("/oee/daily", {"start_date": START_DATE.isoformat(), "end_date": END_DATE.isoformat()}),
    ("/oee/summary", {"start_date": START_DATE.isoformat(), "end_date": END_DATE.isoformat()}),
    ("/scrap/root-cause", {"start_date": START_DATE.isoformat(), "end_date": END_DATE.isoformat()}),
]


def measure_latency():
    """Measure cache-cold and cache-warm latency for each endpoint."""
    results = []
    
    with httpx.Client(timeout=30.0) as client:
        # Clear any existing cache by restarting the app, or wait for TTL
        print("📊 Measuring endpoint latency...")
        print("=" * 60)
        
        for endpoint, params in ENDPOINTS:
            url = f"{BASE_URL}{endpoint}"
            
            # Cache-cold (first request)
            print(f"\n🔍 Testing: {endpoint}")
            print(f"   Params: {params}")
            
            start = time.perf_counter()
            response = client.get(url, params=params)
            cold_time = time.perf_counter() - start
            
            print(f"   Cache-cold: {cold_time:.3f}s")
            
            # Cache-warm (immediate second request)
            start = time.perf_counter()
            response = client.get(url, params=params)
            warm_time = time.perf_counter() - start
            
            print(f"   Cache-warm: {warm_time:.3f}s")
            print(f"   Speedup: {cold_time / warm_time:.1f}x")
            print(f"   Status: {response.status_code}")
            print(f"   Response size: {len(response.text)} chars")
            
            results.append({
                "endpoint": endpoint,
                "cold_time": cold_time,
                "warm_time": warm_time,
                "speedup": cold_time / warm_time if warm_time > 0 else 0,
                "status": response.status_code,
                "response_size": len(response.text),
            })
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"{'Endpoint':<25} {'Cold (s)':<10} {'Warm (s)':<10} {'Speedup':<10}")
    print("-" * 60)
    for r in results:
        print(f"{r['endpoint']:<25} {r['cold_time']:<10.3f} {r['warm_time']:<10.3f} {r['speedup']:<10.1f}x")


if __name__ == "__main__":
    measure_latency()