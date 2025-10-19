-- models/staging/stg_patient_vitals.sql
with src as (
  select
    value_patient_id as patient_id,
    -- cast timestamp if needed; keep as TIMESTAMP
    safe_cast(timestamp as TIMESTAMP) as ts,
    value_gps_lat as gps_lat,
    value_gps_long as gps_long,
  from {{ source('patients_vitals', 'patient_vitals') }}
)
select
  patient_id,
  ts as timestamp,
  gps_lat,
  gps_long,
from src
where gps_lat is not null and gps_long is not null
