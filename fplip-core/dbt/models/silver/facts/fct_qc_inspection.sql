{{
  config(
    materialized='table'
  )
}}

select
  {{ dbt_utils.generate_surrogate_key([
    'inspection_id'
  ]) }} as inspection_id,
  machine_id,
  production_run_reference,
  inspection_date,
  defect_type_id,
  units_inspected,
  units_rejected,
  inspector_id,
  data_entry_method,
  entered_by,
  entered_at,
  -- Derived: rejection rate
  case 
    when units_inspected > 0 then cast(units_rejected as float64) / cast(units_inspected as float64)
    else null
  end as rejection_rate
from {{ ref('stg_qc_inspections') }}
