{{ config(
    materialized='incremental',
    unique_key='memory_id',
    incremental_strategy='merge',
    post_hook=[
      "CREATE VECTOR INDEX IF NOT EXISTS text_embedding_vector_index ON `Alzora_Embeddings_Dataset`.`memories_embeddings`(text_embedding) OPTIONS(index_type = 'IVF', distance_type = 'COSINE');",

      "CREATE VECTOR INDEX IF NOT EXISTS image_embedding_vector_index ON `Alzora_Embeddings_Dataset`.`memories_embeddings`(image_embedding) OPTIONS(index_type = 'IVF', distance_type = 'COSINE');",

      "ALTER VECTOR INDEX IF EXISTS text_embedding_vector_index ON `Alzora_Embeddings_Dataset`.`memories_embeddings` REBUILD;",

      "ALTER VECTOR INDEX IF EXISTS image_embedding_vector_index ON `Alzora_Embeddings_Dataset`.`memories_embeddings` REBUILD;"
    ]
) }}

select
    memory_id,
    array(
        select safe_cast(json_value(elem) as float64)
        from unnest(json_query_array(text_embedding)) as elem
    ) as text_embedding,
    array(
        select safe_cast(json_value(elem) as float64)
        from unnest(json_query_array(image_embedding)) as elem
    ) as image_embedding,
    created_at
from {{ ref('stg_embeddings') }}

{% if is_incremental() %}
    where cast(created_at as timestamp) > (
        select coalesce(max(cast(created_at as timestamp)), timestamp('1900-01-01 00:00:00')) 
        from {{ this }}
    )
{% endif %}
