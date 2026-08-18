select
  defect_type_id,
  defect_name,
  defect_category,
  severity,
  description,
  active_flag,
  _ingested_at,
  _source_file
from {{ ref('defect_types') }}