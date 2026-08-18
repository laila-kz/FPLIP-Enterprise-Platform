-- A dbt singular test passes when it returns zero rows.
-- This test checks that the grain of fct_production_run is truly unique.

select
  machine_id,
  shift_id,
  product_id,
  run_date,
  run_sequence_number,
  count(*) as row_count
from {{ ref('fct_production_run') }}
group by 1, 2, 3, 4, 5
having count(*) > 1