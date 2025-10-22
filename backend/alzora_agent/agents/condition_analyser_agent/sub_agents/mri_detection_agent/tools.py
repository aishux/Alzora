from google.adk.tools import ToolContext
from alzora_agent.setup import *
from PIL import Image
import io


def mri_search(tool_context: ToolContext, query: str):
    """To search the mri scan image to identify patient's condition"""
    try:
        patient_id = tool_context.state["patient_information"]["patient_id"]
        for part in tool_context.user_content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                blob = part.inline_data
                file_bytes = blob.data
                image_obj = Image.open(io.BytesIO(file_bytes))
                print("Assinged Image Object")

        embeddings = get_image_embeddings(image_obj, query)

        search_results = get_bigquery_data(f'''
                WITH query_emb AS (
                    SELECT {embeddings["Image Embedding"]} AS q_emb
                )
                SELECT
                    base.mri_scan_type,
                    distance
                    FROM VECTOR_SEARCH(
                        TABLE `alzora_datawarehouse.mri_image_embeddings`
                        'mri_embeddings',
                        TABLE query_emb,
                        top_k => 1,
                        distance_type => 'COSINE'
                    );
        ''')

        return {"Detected Condition": dict(list(search_results)[0])["mri_scan_type"]}

    except Exception as e:
        print("Exception is: " + str(e))
        return "Couldn't parse your image file"