# ADR-007: Gold Dimension Join Pattern

## Status
Accepted (2026-07-31)

## Finding
- `dim_product` has **1 version per product** → **Type 1** (no SCD2 history)
- `dim_machine` has **1 version per machine** → **Type 1** (no SCD2 history)

## Decision
Gold models will join to `dim_product` and `dim_machine` using a **simple equi-join**:

```sql
-- Join to dim_product
ON fct_production_run.product_id = dim_product.product_id

-- Join to dim_machine  
ON fct_production_run.machine_id = dim_machine.machine_id

## Comment :
every product_id and machine_id has exactly ONE row in the dimension tables. This means:

✅ No SCD2 history exists in your dimensions  -> No SCD2 history exists in the dimension tables (each product_id and machine_id has exactly one row). Therefore, no date-ranged join is needed.



✅ Simple equi-join is the correct pattern for Gold models

✅ You don't need date-ranged joins