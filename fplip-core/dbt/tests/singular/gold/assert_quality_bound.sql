-- This test fails if Quality > 1 at the aggregated level
-- (good_units should never exceed produced_units)

select
  pr.machine_id,
  pr.shift_id,
  pr.run_date as date_id,
  sum(pr.good_units) as total_good,
  sum(pr.produced_units) as total_produced,
  sum(pr.good_units) / nullif(sum(pr.produced_units), 0) as quality
from {{ ref('fct_production_run') }} pr
group by 1, 2, 3
having total_good > total_produced