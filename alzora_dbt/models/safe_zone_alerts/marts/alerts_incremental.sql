-- models/marts/alerts_incremental.sql
{{ config(
    materialized='incremental',
    unique_key=['patient_id','event_ts']
) }}

with breaches as (
  select
    patient_id,
    event_ts,
    gps_lat,
    gps_long,
    distance_meters,
    safe_radius_meters,
    current_timestamp() as created_at
  from {{ ref('breaches') }}
  where is_outside_safe_zone = true
)

{% if is_incremental() %}
  -- only consider new events since last run to limit work
  select * from breaches
  where event_ts > (select max(event_ts) from {{ this }})
{% else %}
  select * from breaches
{% endif %}

