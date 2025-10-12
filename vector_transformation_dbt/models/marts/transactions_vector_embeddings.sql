{{ config(
    materialized='incremental',
    unique_key='txn_id',
    incremental_strategy='merge',
    post_hook=[
      "CREATE VECTOR INDEX IF NOT EXISTS embedding_vector_index ON `Embeddings_Dataset`.`transactions_vector_embeddings`(embedding) OPTIONS(index_type = 'IVF', distance_type = 'COSINE');",

      "ALTER VECTOR INDEX IF EXISTS embedding_vector_index ON `Embeddings_Dataset`.`transactions_vector_embeddings` REBUILD;"
    ]
) }}

select
    txn_id,
    array(
        select safe_cast(json_value(elem) as float64)
        from unnest(json_query_array(embedding_json)) as elem
    ) as embedding,
    created_at
from {{ ref('stg_embeddings') }}

{% if is_incremental() %}
    where cast(created_at as timestamp) > (
        select coalesce(max(cast(created_at as timestamp)), timestamp('1900-01-01 00:00:00')) 
        from {{ this }}
    )
{% endif %}
