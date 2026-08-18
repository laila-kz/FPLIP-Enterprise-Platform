-- This test fails if total_units_rejected exceeds total_units_inspected
-- (defect counts should never exceed inspected units)

select
  machine_id,
  shift_id,
  date_id,
  product_id,
  defect_type_id,
  total_units_inspected,
  total_units_rejected
from {{ ref('scrap_root_cause_summary') }}
where total_units_rejected > total_units_inspected