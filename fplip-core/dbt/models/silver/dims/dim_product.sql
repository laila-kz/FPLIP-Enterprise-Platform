select
  product_id,
  product_name,
  product_family,
  unit_of_measure,
  standard_cycle_time_sec,
  cycle_time_source,
  cycle_time_confidence,
  standard_weight_kg,
  active_flag,
  data_entry_method,
  created_at,
  last_updated_at,
  valid_from,
  valid_to,
  is_current
from {{ ref('dim_product_history') }}
where is_current = true