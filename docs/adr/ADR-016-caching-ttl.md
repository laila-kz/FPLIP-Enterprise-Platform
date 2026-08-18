# ADR-016: Caching TTL

## Status
Accepted (2026-08-08)

## Decision
API responses are cached in-memory with a TTL of **4 hours (14,400 seconds)**.

## Reasoning
- Gold tables refresh once per day (Week 6's production schedule)
- 4 hours is well under 24 hours, so cached data is never staler than "same day"
- Provides significant performance improvement for repeated queries (94-263x)
- Short enough that manual data fixes are reflected within the same day

## Implementation
- `TTLCache` class in `api/cache/ttl_cache.py`
- Cache keyed on endpoint + all parameters (MD5 hash)
- Separate cache instances for OEE and Scrap endpoints

## Performance Results
| Endpoint | Cache-Cold | Cache-Warm | Speedup |
|----------|------------|------------|---------|
| `/oee/daily` | 4.447s | 0.017s | 263x |
| `/oee/summary` | 1.619s | 0.017s | 94x |
| `/scrap/root-cause` | 1.624s | 0.008s | 192x |

## Date
2026-08-08