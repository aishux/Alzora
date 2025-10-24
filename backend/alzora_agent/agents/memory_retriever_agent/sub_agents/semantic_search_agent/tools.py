from google.adk.tools import ToolContext
from alzora_agent.setup import *
from PIL import Image
import io


def get_memory_details(query_result):
    memory_id = dict(list(query_result)[0])["memory_id"]
    memory_details = get_bigquery_data(f'''
        SELECT memory_id, patient_id, text_content 
        FROM alzora_datawarehouse.memories
        WHERE memory_id={memory_id}
    ''')
    return dict(list(memory_details)[0])


def search_memory(tool_context: ToolContext, query: str):
    """To search the memory for a patient using text or image"""
    try:
        image_obj = None
        patient_id = tool_context.state["patient_information"]["patient_id"]
        for part in tool_context.user_content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                blob = part.inline_data
                file_bytes = blob.data
                image_obj = Image.open(io.BytesIO(file_bytes))
                print("Assinged Image Object")
        
        print("Image object is:", image_obj)
        text_content = query

        if image_obj:
            embeddings = get_image_embeddings(image_obj, text_content)

            search_results = get_bigquery_data(f'''
                    WITH query_emb AS (
                        SELECT {embeddings["Image Embedding"]} AS q_emb
                    )
                    SELECT
                        base.memory_id,
                        distance
                        FROM VECTOR_SEARCH(
                            (
                                SELECT *
                                FROM `Alzora_Embeddings_Dataset_alzora_datawarehouse.memories_embeddings`
                                WHERE patient_id = {patient_id} AND ARRAY_LENGTH(image_embedding) != 0
                            ),
                        'image_embedding',
                        TABLE query_emb,
                        top_k => 1,
                        distance_type => 'COSINE'
                    );
            ''')
        else:
            embeddings = get_text_embeddings(text_content)
            search_results = get_bigquery_data(f'''
                    WITH query_emb AS (
                        SELECT {embeddings} AS q_emb
                    )
                    SELECT
                        base.memory_id,
                        distance
                        FROM VECTOR_SEARCH(
                            (
                                SELECT *
                                FROM `Alzora_Embeddings_Dataset_alzora_datawarehouse.memories_embeddings`
                                WHERE patient_id = {patient_id} AND ARRAY_LENGTH(text_embedding) != 0
                            ),
                        'text_embedding',
                        TABLE query_emb,
                        top_k => 1,
                        distance_type => 'COSINE'
                    );
            ''')

        memory_details = get_memory_details(search_results)

        return memory_details

    except Exception as e:
        print("Exception is: " + str(e))
        return "Couldn't parse your image file"