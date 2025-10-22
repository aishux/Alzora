{{ config(materialized='view') }}

with source_data as (
    select
        memory_id,
        patient_id,
        text_embedding,
        image_embedding,
        created_at
    from {{ source('raw_data', 'memories') }}
    where text_embedding is not null
      and image_embedding is not null
      and memory_id is not null
      and patient_id is not null
      and created_at is not null
)

select
    memory_id,
    patient_id,
    text_embedding,
    image_embedding,
    created_at
from source_data
