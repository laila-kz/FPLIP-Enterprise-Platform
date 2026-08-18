-- This test fails if loss attribution doesn't match total downtime
-- Recomputes independently from raw data, not from oee_daily itself

with downtime_total as (
  select
    machine_id,
    shift_id,
    event_date,
    sum(duration_sec) as total_downtime
  from {{ ref('fct_downtime_event') }}
  group by 1, 2, 3
),

loss_attribution as (
  select
    de.machine_id,
    de.shift_id,
    de.event_date,
    sum(case when dr.oee_loss_category = 'Availability Loss' then de.duration_sec else 0 end) as avail_loss,
    sum(case when dr.oee_loss_category = 'Performance Loss' then de.duration_sec else 0 end) as perf_loss,
    sum(case when dr.oee_loss_category in ('Availability Loss', 'Performance Loss') then 0 else de.duration_sec end) as unmapped_loss
  from {{ ref('fct_downtime_event') }} de
  left join {{ ref('dim_downtime_reason') }} dr
    on de.reason_id = dr.reason_id
  group by 1, 2, 3
)

select
  dt.machine_id,
  dt.shift_id,
  dt.event_date as date_id,
  dt.total_downtime,
  la.avail_loss,
  la.perf_loss,
  la.unmapped_loss,
  la.avail_loss + la.perf_loss + la.unmapped_loss as calculated_total,
  dt.total_downtime - (la.avail_loss + la.perf_loss + la.unmapped_loss) as difference
from downtime_total dt
left join loss_attribution la
  on dt.machine_id = la.machine_id
  and dt.shift_id = la.shift_id
  and dt.event_date = la.event_date
where abs(dt.total_downtime - (coalesce(la.avail_loss, 0) + coalesce(la.perf_loss, 0) + coalesce(la.unmapped_loss, 0))) > 1