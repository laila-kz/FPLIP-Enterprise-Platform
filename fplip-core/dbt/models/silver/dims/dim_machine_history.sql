{{
  config(
    materialized='table'
  )
}}

{% if not adapter.get_relation(this.database, this.schema, this.identifier) %}

-- First run: simple snapshot
select
  machine_id,
  machine_name,
  machine_type,
  line_id,
  location,
  manufacturer,
  install_date,
  status,
  nominal_capacity_units_per_hour,
  data_entry_method,
  last_updated_at,
  last_updated_by,
  _ingested_at,
  _source_file,
  snapshot_taken_at as valid_from,
  cast(null as timestamp) as valid_to,
  true as is_current
from {{ ref('_current_machine_snapshot') }}

{% else %}

-- Simplified approach: rebuild from scratch each time
-- This is DDL-only (CREATE OR REPLACE) and preserves history
-- by unioning previous history with current changes

with current_state as (
  select
    machine_id,
    machine_name,
    machine_type,
    line_id,
    location,
    manufacturer,
    install_date,
    status,
    nominal_capacity_units_per_hour,
    data_entry_method,
    last_updated_at,
    last_updated_by,
    _ingested_at,
    _source_file,
    snapshot_taken_at
  from {{ ref('_current_machine_snapshot') }}
),

previous_history as (
  select * from {{ this }}
),

-- Identify changed machines
changed_machines as (
  select distinct
    p.machine_id
  from previous_history p
  join current_state c
    on p.machine_id = c.machine_id
  where p.is_current = true
    and (
      p.machine_name != c.machine_name
      or p.machine_type != c.machine_type
      or coalesce(p.line_id, '') != coalesce(c.line_id, '')
      or coalesce(p.location, '') != coalesce(c.location, '')
      or coalesce(p.manufacturer, '') != coalesce(c.manufacturer, '')
      or p.status != c.status
      or coalesce(cast(p.nominal_capacity_units_per_hour as string), '') != coalesce(cast(c.nominal_capacity_units_per_hour as string), '')
    )
),

-- Preserve unchanged rows (all historical rows that haven't changed)
preserved_rows as (
  select
    p.machine_id,
    p.machine_name,
    p.machine_type,
    p.line_id,
    p.location,
    p.manufacturer,
    p.install_date,
    p.status,
    p.nominal_capacity_units_per_hour,
    p.data_entry_method,
    p.last_updated_at,
    p.last_updated_by,
    p._ingested_at,
    p._source_file,
    p.valid_from,
    p.valid_to,
    p.is_current
  from previous_history p
  left join changed_machines ch
    on p.machine_id = ch.machine_id
  where ch.machine_id is null
),

-- Close changed rows
closed_rows as (
  select
    p.machine_id,
    p.machine_name,
    p.machine_type,
    p.line_id,
    p.location,
    p.manufacturer,
    p.install_date,
    p.status,
    p.nominal_capacity_units_per_hour,
    p.data_entry_method,
    p.last_updated_at,
    p.last_updated_by,
    p._ingested_at,
    p._source_file,
    p.valid_from,
    c.snapshot_taken_at as valid_to,
    false as is_current
  from previous_history p
  join current_state c
    on p.machine_id = c.machine_id
  join changed_machines ch
    on p.machine_id = ch.machine_id
  where p.is_current = true
),

-- New current rows (changed machines + new machines)
new_current_rows as (
  select
    c.machine_id,
    c.machine_name,
    c.machine_type,
    c.line_id,
    c.location,
    c.manufacturer,
    c.install_date,
    c.status,
    c.nominal_capacity_units_per_hour,
    c.data_entry_method,
    c.last_updated_at,
    c.last_updated_by,
    c._ingested_at,
    c._source_file,
    c.snapshot_taken_at as valid_from,
    cast(null as timestamp) as valid_to,
    true as is_current
  from current_state c
  left join previous_history p
    on c.machine_id = p.machine_id
    and p.is_current = true
  where p.machine_id is null
     or c.machine_id in (select machine_id from changed_machines)
)

-- Final result: union all parts (types are now explicitly consistent)
select * from preserved_rows
union all
select * from closed_rows
union all
select * from new_current_rows

{% endif %}