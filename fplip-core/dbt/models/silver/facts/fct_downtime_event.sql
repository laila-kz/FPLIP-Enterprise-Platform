{{
  config(
    materialized='table'
  )
}}

select
  {{ dbt_utils.generate_surrogate_key([
    'machine_id', 
    'shift_id', 
    'event_date', 
    'start_time'
  ]) }} as event_id,
  machine_id,
  shift_id,
  event_date,
  reason_id,
  reason_free_text,
  start_time,
  end_time,
  duration_sec
from {{ ref('stg_downtime_events') }}