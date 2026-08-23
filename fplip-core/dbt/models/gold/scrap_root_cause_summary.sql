{{
  config(
    materialized='table',
    cluster_by=['date_id', 'machine_id', 'product_id']
  )
}}

with run_by_machine_date as (
  select
    machine_id,
    run_date,
    any_value(shift_id) as shift_id,
    any_value(product_id) as product_id,
    sum(produced_units) as produced_units,
    sum(good_units) as good_units
  from {{ ref('fct_production_run') }}
  group by machine_id, run_date
),

inspection_with_run as (
  select
    qi.inspection_id,
    qi.production_run_reference,
    qi.inspection_date,
    qi.defect_type_id,
    qi.units_inspected,
    qi.units_rejected,
    qi.rejection_rate,
    qi.machine_id as qc_machine_id,
    coalesce(pr.machine_id, fb.machine_id) as run_machine_id,
    coalesce(pr.shift_id, fb.shift_id) as run_shift_id,
    coalesce(pr.product_id, fb.product_id) as run_product_id,
    coalesce(pr.produced_units, fb.produced_units) as produced_units,
    coalesce(pr.good_units, fb.good_units) as good_units,
    coalesce(pr.produced_units - pr.good_units, fb.produced_units - fb.good_units) as scrap_units
  from {{ ref('fct_qc_inspection') }} qi
  left join {{ ref('fct_production_run') }} pr
    on qi.production_run_reference = pr.log_reference_number
    or qi.production_run_reference = pr.run_id
  left join run_by_machine_date fb
    on qi.machine_id = fb.machine_id
   and qi.inspection_date = fb.run_date
),

defect_classified as (
  select
    coalesce(iwr.run_machine_id, iwr.qc_machine_id, 'UNKNOWN') as machine_id,
    coalesce(iwr.run_shift_id, 'UNKNOWN') as shift_id,
    iwr.inspection_date as date_id,
    coalesce(iwr.run_product_id, 'UNKNOWN') as product_id,
    coalesce(dt.defect_category, 'N/A - Pass') as defect_category,
    coalesce(dt.defect_type_id, 'PASS') as defect_type_id,
    coalesce(dt.defect_name, 'Passed Inspection') as defect_name,
    coalesce(dt.severity, 'None') as severity,
    iwr.units_inspected,
    iwr.units_rejected,
    coalesce(iwr.produced_units, 0) as produced_units,
    coalesce(iwr.good_units, 0) as good_units,
    coalesce(iwr.scrap_units, 0) as scrap_units
  from inspection_with_run iwr
  left join {{ ref('dim_defect_type') }} dt
    on iwr.defect_type_id = dt.defect_type_id
)

select
  machine_id,
  shift_id,
  date_id,
  product_id,
  defect_type_id,
  defect_name,
  defect_category,
  severity,
  sum(units_inspected) as total_units_inspected,
  sum(units_rejected) as total_units_rejected,
  sum(units_rejected) / nullif(sum(units_inspected), 0) as rejection_rate,
  sum(scrap_units) as total_scrap_units,
  sum(scrap_units) / nullif(sum(produced_units), 0) as scrap_percentage,
  count(*) as inspection_count,
  current_timestamp() as _updated_at
from defect_classified
group by
  machine_id,
  shift_id,
  date_id,
  product_id,
  defect_type_id,
  defect_name,
  defect_category,
  severity