select
  inspection_id,
  machine_id,
  production_run_reference,
  inspection_date,
  defect_type_id,
  units_inspected,
  units_rejected,
  inspector_id,
  data_entry_method,
  entered_by,
  entered_at
from {{ source('bronze', 'qc_inspections') }}
