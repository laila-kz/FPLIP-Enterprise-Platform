-- This test fails if any OEE component is outside expected bounds
-- Returns rows that violate the rules

select
  machine_id,
  shift_id,
  date_id,
  availability,
  performance,
  quality,
  oee
from {{ ref('oee_daily') }}
where 
  -- Availability should be between 0 and 1
  availability < 0 or availability > 1
  -- Quality should be between 0 and 1
  or quality < 0 or quality > 1
  -- OEE should be between 0 and 1
  or oee < 0 or oee > 1
  -- Performance can exceed 1 (machine running faster than standard cycle time)
  -- So we don't bound it