from google.adk.tools import ToolContext
from alzora_agent.setup import *
from PIL import Image
import io

from datetime import datetime


def register_memory(tool_context: ToolContext, text_content: str):
    """To register the memory for a patient"""
    try:
        image_obj=None
        patient_id = tool_context.state["patient_information"]["patient_id"]
        for part in tool_context.user_content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                blob = part.inline_data
                file_bytes = blob.data
                image_obj = Image.open(io.BytesIO(file_bytes))

        table = get_tidb_table("memories")

        image_embeddings = None

        if image_obj:
            embeddings = get_image_embeddings(image_obj, text_content)
            image_embeddings = embeddings["Image Embedding"]
            text_embeddings = embeddings["Text Embedding"]
        else:
            text_embeddings = get_text_embeddings(text_content)
        table.insert(
            {
                "patient_id": patient_id,
                "text_content": text_content,
                "text_embedding": text_embeddings,
                "image_embedding": image_embeddings,
                "created_at": str(datetime.now()),
                "updated_at": str(datetime.now()),
            }
        )
    
        return "Memory Registered Successfully!"

    except Exception as e:
        print("Exception is: " + str(e))
        return "Couldn't parse your image file"