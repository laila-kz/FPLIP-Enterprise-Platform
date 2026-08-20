select
  reason_id,
  reason_name,
  reason_category,
  oee_loss_category,
  description,
  active_flag,
  _ingested_at,
  _source_file
from {{ source('bronze', 'downtime_reasons') }}