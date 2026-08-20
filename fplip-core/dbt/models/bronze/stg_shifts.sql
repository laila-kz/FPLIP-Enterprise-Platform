select
  shift_id,
  shift_name,
  start_time,
  end_time,
  crosses_midnight,
  active_flag,
  _ingested_at,
  _source_file
from {{ source('bronze', 'shifts') }}