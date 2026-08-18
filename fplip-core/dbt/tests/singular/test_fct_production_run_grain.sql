select
  machine_id,
  shift_id,
  product_id,
  run_date,
  run_sequence_number,
  count(*) as row_count
from {{ ref('fct_production_run') }}
group by
  machine_id,
  shift_id,
  product_id,
  run_date,
  run_sequence_number
having count(*) > 1
