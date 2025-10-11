{{ config(materialized='view') }}

with source_data as (
    select
        txn_id,
        embedding,
        created_at
    from {{ source('raw_data', 'transaction_embeddings') }}
    where embedding is not null
      and txn_id is not null
      and created_at is not null
)

select
    txn_id,
    embedding as embedding_json,
    created_at
from source_data
