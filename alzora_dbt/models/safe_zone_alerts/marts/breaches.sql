-- models/marts/breaches.sql
with latest as (
  select * from {{ ref('latest_vitals') }}
),
patients as (
  select * from {{ ref('stg_patients') }}
)
select
  l.patient_id,
  l.timestamp as event_ts,
  l.gps_lat,
  l.gps_long,
  p.safe_center_lat,
  p.safe_center_long,
  p.safe_radius_meters,
  {{ st_distance_meters('p.safe_center_long','p.safe_center_lat','l.gps_long','l.gps_lat') }} as distance_meters,
  case
    when {{ st_distance_meters('p.safe_center_long','p.safe_center_lat','l.gps_long','l.gps_lat') }} > p.safe_radius_meters then true
    else false
  end as is_outside_safe_zone
from latest l
join patients p on l.patient_id = p.patient_id
where l.gps_lat is not null and l.gps_long is not null
