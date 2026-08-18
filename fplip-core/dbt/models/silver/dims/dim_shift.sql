select
  shift_id,
  shift_name,
  start_time,
  end_time,
  crosses_midnight,
  active_flag
from {{ ref('stg_shifts') }}