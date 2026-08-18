# ADR-015: API Key Storage

## Status
Accepted (2026-08-05)

## Decision
API uses a single static key for app-level authentication, stored as an environment variable (`API_KEY`).

## Reasoning
- This project serves a single user/team (no multi-tenant requirements)
- Single static key is sufficient for the current scope
- Environment variable storage is secure and simple
- No external dependency (like Redis) needed for key storage

## Implementation
- `API_KEY` set in `.env` (gitignored)
- `.env.example` provides placeholder (committed)
- FastAPI dependency checks `X-API-Key` header against `Settings.api_key`

## Date
2026-08-05