select
  event_id,
  machine_id,
  shift_id,
  event_date,
  reason_id,
  reason_free_text,
  start_time,
  end_time,
  duration_sec,
  data_entry_method,
  entered_by,
  entered_at,
  _ingested_at,
  _source_file
from {{ ref('downtime_events') }}