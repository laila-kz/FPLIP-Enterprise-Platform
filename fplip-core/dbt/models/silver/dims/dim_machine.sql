select
  machine_id,
  machine_name,
  machine_type,
  line_id,
  location,
  manufacturer,
  install_date,
  status,
  nominal_capacity_units_per_hour,
  data_entry_method,
  last_updated_at,
  last_updated_by,
  valid_from,
  valid_to,
  is_current
from {{ ref('dim_machine_history') }}
where is_current = true