{{
  config(
    materialized='view'
  )
}}

select
  *,
  current_timestamp() as snapshot_taken_at
from {{ ref('stg_machines') }}