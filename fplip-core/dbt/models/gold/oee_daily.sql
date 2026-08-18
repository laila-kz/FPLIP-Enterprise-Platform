{{
  config(
    materialized='table',
    cluster_by=['date_id', 'machine_id']
  )
}}

-- TEST VERSION — Simplified to debug Availability

with machine_shift_day as (
  select distinct
    machine_id,
    shift_id,
    run_date as date_id
  from {{ ref('fct_production_run') }}
),

shift_duration as (
  select
    shift_id,
    case
      when safe_cast(end_time as time) < safe_cast(start_time as time)
        then (
          24 - extract(hour from safe_cast(start_time as time))
          + extract(hour from safe_cast(end_time as time))
        ) * 3600
      else (
        extract(hour from safe_cast(end_time as time))
        - extract(hour from safe_cast(start_time as time))
      ) * 3600
    end as shift_duration_sec
  from {{ ref('dim_shift') }}
),

downtime_agg as (
  select
    machine_id,
    shift_id,
    event_date as date_id,
    sum(duration_sec) as total_downtime_sec
  from {{ ref('fct_downtime_event') }}
  group by 1, 2, 3
),

availability as (
  select
    msd.machine_id,
    msd.shift_id,
    msd.date_id,
    sd.shift_duration_sec,
    coalesce(downtime.total_downtime_sec, 0) as total_downtime_sec,
    (sd.shift_duration_sec - coalesce(downtime.total_downtime_sec, 0)) 
      / nullif(sd.shift_duration_sec, 0) as availability
  from machine_shift_day msd
  left join shift_duration sd on msd.shift_id = sd.shift_id
  left join downtime_agg downtime 
    on msd.machine_id = downtime.machine_id
    and msd.shift_id = downtime.shift_id
    and cast(msd.date_id as date) = cast(downtime.date_id as date)  -- Explicit cast to DATE
),

run_performance as (
  select
    pr.machine_id,
    pr.shift_id,
    cast(pr.run_date as date) as date_id,
    pr.produced_units,
    pr.good_units,
    timestamp_diff(pr.run_end_time, pr.run_start_time, second) as run_duration_sec,
    safe_cast(p.standard_cycle_time_sec as float64) as standard_cycle_time_sec,
    p.cycle_time_confidence
  from {{ ref('fct_production_run') }} pr
  left join {{ ref('dim_product') }} p on pr.product_id = p.product_id
  where pr.run_start_time is not null
    and pr.run_end_time is not null
    and timestamp_diff(pr.run_end_time, pr.run_start_time, second) > 0
    and safe_cast(p.standard_cycle_time_sec as float64) > 0
    and pr.produced_units > 0
),

-- Calculate the run-level performance ratio first so the daily roll-up can
-- weight each run by its actual duration and avoid skew from short runs.
run_performance_metrics as (
  select
    machine_id,
    shift_id,
    date_id,
    produced_units,
    good_units,
    run_duration_sec,
    standard_cycle_time_sec,
    cycle_time_confidence,
    case
      when run_duration_sec > 0 and standard_cycle_time_sec > 0
        then least(
          (produced_units * standard_cycle_time_sec) / nullif(run_duration_sec, 0),
          1.0
        )
      else null
    end as calculated_performance
  from run_performance
),

performance_quality as (
  select
    machine_id,
    shift_id,
    date_id,
    sum(calculated_performance * run_duration_sec) / nullif(sum(run_duration_sec), 0) as performance,
    sum(good_units) / nullif(sum(produced_units), 0) as quality,
    min(cycle_time_confidence) as cycle_time_confidence
  from run_performance_metrics
  group by 1, 2, 3
),

loss_attribution as (
  select
    de.machine_id,
    de.shift_id,
    de.event_date as date_id,
    sum(case 
      when dr.oee_loss_category = 'Availability Loss' then de.duration_sec
      else 0
    end) as availability_loss_sec,
    sum(case 
      when dr.oee_loss_category = 'Performance Loss' then de.duration_sec
      else 0
    end) as performance_loss_sec,
    sum(case 
      when dr.oee_loss_category is null 
        or dr.oee_loss_category = '' 
        or de.reason_id is null then de.duration_sec
      else 0
    end) as unmapped_loss_sec
  from {{ ref('fct_downtime_event') }} de
  left join {{ ref('dim_downtime_reason') }} dr on de.reason_id = dr.reason_id
  group by 1, 2, 3
)

select
  a.machine_id, 
  a.shift_id,
  a.date_id,
  a.availability,
  a.shift_duration_sec,
  a.total_downtime_sec,
  pq.performance,
  pq.quality,
  coalesce(pq.cycle_time_confidence, 'unconfirmed') as cycle_time_confidence,
  coalesce(loss.availability_loss_sec, 0) as availability_loss_sec,
  coalesce(loss.performance_loss_sec, 0) as performance_loss_sec,
  coalesce(loss.unmapped_loss_sec, 0) as unmapped_loss_sec,
  coalesce(loss.availability_loss_sec, 0) + coalesce(loss.performance_loss_sec, 0) + coalesce(loss.unmapped_loss_sec, 0) as total_loss_sec,
  case
    when a.availability is not null 
     and pq.performance is not null 
     and pq.quality is not null
    then a.availability * pq.performance * pq.quality
    else null
  end as oee
from availability a
left join performance_quality pq
  on a.machine_id = pq.machine_id
  and a.shift_id = pq.shift_id
  and cast(a.date_id as date) = cast(pq.date_id as date)
left join loss_attribution loss
  on a.machine_id = loss.machine_id
  and a.shift_id = loss.shift_id
  and cast(a.date_id as date) = cast(loss.date_id as date)