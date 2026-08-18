{{
  config(
    materialized='table',
    cluster_by=['date_id', 'machine_id', 'product_id']
  )
}}

/*
  SCRAP ROOT CAUSE SUMMARY — Week 6 Build
  
  Grain: machine + shift + date + product + defect_type
  
  Design Decision: This mart includes ALL inspections, including passes.
  Pass records have defect_type_id = NULL and are grouped into a special
  'N/A - Pass' category.
  
  IMPORTANT: QC inspections do NOT have machine_id/shift_id/product_id directly.
  They join to fct_production_run via production_run_reference to get these.
  If production_run_reference is NULL, use 'UNKNOWN' for machine/shift/product.
*/

with inspection_with_run as (
  select
    qi.inspection_id,
    qi.production_run_reference,
    qi.inspection_date,
    qi.defect_type_id,
    qi.units_inspected,
    qi.units_rejected,
    qi.rejection_rate,
    -- Get machine/shift/product from production run if available
    pr.machine_id,
    pr.shift_id,
    pr.product_id,
    pr.produced_units,
    pr.good_units,
    pr.produced_units - pr.good_units as scrap_units
  from {{ ref('fct_qc_inspection') }} qi
  left join {{ ref('fct_production_run') }} pr
    on qi.production_run_reference = pr.run_id
),

defect_classified as (
  select
    -- Use machine_id from production run, or 'UNKNOWN' if no match
    coalesce(iwr.machine_id, 'UNKNOWN') as machine_id,
    coalesce(iwr.shift_id, 'UNKNOWN') as shift_id,
    iwr.inspection_date as date_id,
    coalesce(iwr.product_id, 'UNKNOWN') as product_id,
    -- Map defect_type_id to category, or 'N/A - Pass' for null
    coalesce(
      dt.defect_category,
      'N/A - Pass'
    ) as defect_category,
    coalesce(
      dt.defect_type_id,
      'PASS'
    ) as defect_type_id,
    coalesce(
      dt.defect_name,
      'Passed Inspection'
    ) as defect_name,
    coalesce(
      dt.severity,
      'None'
    ) as severity,
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
  -- Aggregations
  sum(units_inspected) as total_units_inspected,
  sum(units_rejected) as total_units_rejected,
  sum(units_rejected) / nullif(sum(units_inspected), 0) as rejection_rate,
  sum(scrap_units) as total_scrap_units,
  sum(scrap_units) / nullif(sum(produced_units), 0) as scrap_percentage,
  -- Count of inspections in this group
  count(*) as inspection_count,
  -- Timestamp for lineage
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