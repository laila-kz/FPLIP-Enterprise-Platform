{{
  config(
    materialized='table'
  )
}}

select
  {{ dbt_utils.generate_surrogate_key([
    'machine_id', 
    'shift_id', 
    'product_id', 
    'run_date', 
    'run_sequence_number'
  ]) }} as run_id,
  log_reference_number,
  machine_id,
  shift_id,
  product_id,
  run_date,
  run_sequence_number,
  run_start_time,
  run_end_time,
  planned_units,
  produced_units,
  good_units,
  -- Derived metrics
  produced_units - good_units as scrap_units,
  case 
    when planned_units > 0 then cast(produced_units as float64) / cast(planned_units as float64)
    else null
  end as attainment_rate
from {{ ref('stg_production_runs') }}