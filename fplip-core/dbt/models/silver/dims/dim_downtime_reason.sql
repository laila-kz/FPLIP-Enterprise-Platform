select
  reason_id,
  reason_name,
  reason_category,
  oee_loss_category,
  description,
  active_flag
from {{ ref('stg_downtime_reasons') }}