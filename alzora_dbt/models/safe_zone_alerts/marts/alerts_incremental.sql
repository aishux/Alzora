-- models/marts/alerts_incremental.sql
{{ config(
    materialized='incremental',
    unique_key='alert_id',
    incremental_strategy='insert_overwrite'
) }}

with breaches as (
  select * from {{ ref('breaches') }}
)

select
  GENERATE_UUID() as alert_id,
  b.patient_id,
  b.event_ts,
  b.gps_lat,
  b.gps_long,
  b.safe_center_lat,
  b.safe_center_long,
  b.safe_radius_meters,
  b.distance_meters,
  b.is_outside_safe_zone,
  current_timestamp() as created_at
from breaches b
where b.is_outside_safe_zone = true

{% if is_incremental() %}
  and b.event_ts > (select max(event_ts) from {{ this }})
{% endif %}

