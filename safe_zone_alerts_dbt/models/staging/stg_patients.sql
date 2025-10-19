-- models/staging/stg_patients.sql
with src as (
  select
    patient_id,
    safe_center_lat,
    safe_center_long,
    safe_radius_meters
  from {{ source('alzora_datawarehouse', 'patients') }}
)
select
  patient_id,
  safe_center_lat,
  safe_center_long,
  safe_radius_meters
from src
where patient_id is not null
