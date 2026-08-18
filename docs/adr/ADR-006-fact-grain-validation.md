# ADR-006: Fact Grain Validation & Derivation Rule

## Status
Accepted (2026-07-25)

## Context
The `fct_production_run` fact table is the foundation for all downstream OEE calculations. The grain must be precisely defined and validated against edge cases that would expose a wrong grain definition.

## Decision
The grain for `fct_production_run` is one row per:
- `machine_id`
- `shift_id`  
- `product_id`
- `run_date`
- `run_sequence_number`

### Derivation Rule for `run_sequence_number`

`run_sequence_number` is **sourced directly** from the `stg_production_runs` staging view, which preserves the `run_sequence_number` field from the Bronze source data.

The Bronze source data generates `run_sequence_number` during synthetic data generation, with the following logic:
- Sequence resets per `(machine_id, shift_id, product_id, run_date)`
- A new sequence number is assigned when a new run starts
- Runs are considered distinct when there is a gap in production

### Key Assumptions
1. The source data provides an explicit `run_sequence_number` field
2. Each `(machine_id, shift_id, product_id, run_date, run_sequence_number)` combination is unique
3. No two runs on the same machine/shift/product/day share the same sequence number

## Consequences
### Positive
- Clear, testable uniqueness constraint
- Direct mapping from source to fact without complex derivation
- Enables idempotent fact generation

### Negative
- Relies on source data correctness for sequence numbers
- If source data lacks sequence numbers, derivation logic would need to be implemented

## Validation
The grain was validated against:
1. A deliberately constructed two-run-per-day test case (same machine, same shift, same product, different runs)
2. A second, different multi-run case (three runs on a different machine)

Both cases confirmed the grain produces distinct rows with correct data attribution.