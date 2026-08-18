{% macro refresh_product_history() %}

-- DDL-only SCD2 refresh for product history
-- Preserves unchanged rows, closes changed rows, inserts new current rows

{% set current_snapshot = ref('_current_product_snapshot') %}
{% set history_table = this %}

with current_state as (
  select
    product_id,
    product_name,
    product_family,
    unit_of_measure,
    standard_cycle_time_sec,
    cycle_time_source,
    cycle_time_confidence,
    standard_weight_kg,
    active_flag,
    data_entry_method,
    created_at,
    last_updated_at,
    _ingested_at,
    _source_file,
    snapshot_taken_at
  from {{ current_snapshot }}
),

previous_state as (
  select *
  from {{ history_table }}
),

-- Identify which rows have changed
changed_products as (
  select
    p.product_id
  from previous_state p
  join current_state c
    on p.product_id = c.product_id
  where p.is_current = true
    and (
      p.product_name != c.product_name
      or p.product_family != c.product_family
      or p.unit_of_measure != c.unit_of_measure
      or p.standard_cycle_time_sec != c.standard_cycle_time_sec
      or p.cycle_time_source != c.cycle_time_source
      or p.cycle_time_confidence != c.cycle_time_confidence
      or coalesce(cast(p.standard_weight_kg as string), '') != coalesce(cast(c.standard_weight_kg as string), '')
      or p.active_flag != c.active_flag
    )
),

-- Close out changed rows from previous state
closed_rows as (
  select
    p.product_id,
    p.product_name,
    p.product_family,
    p.unit_of_measure,
    p.standard_cycle_time_sec,
    p.cycle_time_source,
    p.cycle_time_confidence,
    p.standard_weight_kg,
    p.active_flag,
    p.data_entry_method,
    p.created_at,
    p.last_updated_at,
    p._ingested_at,
    p._source_file,
    p.valid_from,
    c.snapshot_taken_at as valid_to,
    false as is_current
  from previous_state p
  join current_state c
    on p.product_id = c.product_id
  join changed_products ch
    on p.product_id = ch.product_id
  where p.is_current = true
),

-- Insert new current rows for changed and new products
new_current_rows as (
  select
    c.product_id,
    c.product_name,
    c.product_family,
    c.unit_of_measure,
    c.standard_cycle_time_sec,
    c.cycle_time_source,
    c.cycle_time_confidence,
    c.standard_weight_kg,
    c.active_flag,
    c.data_entry_method,
    c.created_at,
    c.last_updated_at,
    c._ingested_at,
    c._source_file,
    c.snapshot_taken_at as valid_from,
    null as valid_to,
    true as is_current
  from current_state c
  left join previous_state p
    on c.product_id = p.product_id
    and p.is_current = true
  where p.product_id is null
     or c.product_id in (select product_id from changed_products)
),

-- Preserve all unchanged historical rows
preserved_rows as (
  select
    p.product_id,
    p.product_name,
    p.product_family,
    p.unit_of_measure,
    p.standard_cycle_time_sec,
    p.cycle_time_source,
    p.cycle_time_confidence,
    p.standard_weight_kg,
    p.active_flag,
    p.data_entry_method,
    p.created_at,
    p.last_updated_at,
    p._ingested_at,
    p._source_file,
    p.valid_from,
    p.valid_to,
    p.is_current
  from previous_state p
  left join changed_products ch
    on p.product_id = ch.product_id
  where ch.product_id is null
)

-- Combine all rows
select * from preserved_rows
union all
select * from closed_rows
union all
select * from new_current_rows

{% endmacro %}