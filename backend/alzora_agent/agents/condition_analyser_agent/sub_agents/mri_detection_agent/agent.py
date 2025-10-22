from google.adk.agents import Agent
from .tools import mri_search


mri_detection_agent = Agent(
    name="mri_detection_agent",
    model="gemini-2.5-flash",
    description="MRI Detection Agent",
    instruction="""
       You are an agent that identifies the condition from the given MRI Scan image.
       To identify what the condition of the patient is use the tool mri_search.

       For making the response more customized use the below patient's information:
       {patient_information}
    """,
    tools=[mri_search],
    output_key="mri_condition",
)