-- models/marts/latest_vitals.sql
with ordered as (
  select
    v.*,
    row_number() over (partition by v.patient_id order by v.timestamp desc) as rn
  from {{ ref('stg_patient_vitals') }} v
)
select
  patient_id,
  timestamp,
  gps_lat,
  gps_long,
from ordered
where rn = 1
