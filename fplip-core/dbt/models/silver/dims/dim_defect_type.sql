select
  defect_type_id,
  defect_name,
  defect_category,
  severity,
  description,
  active_flag
from {{ ref('stg_defect_types') }}