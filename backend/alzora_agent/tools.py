from .setup import *
from google.adk.tools import ToolContext


def set_patient_information(tool_context: ToolContext, patient_id: str):

    patient_info = get_bigquery_data(f'''SELECT * from `alzora_datawarehouse.patients` WHERE patient_id={patient_id}''')

    patient_info = dict(list(patient_info)[0])

    tool_context.state["patient_information"] = patient_info

    return True