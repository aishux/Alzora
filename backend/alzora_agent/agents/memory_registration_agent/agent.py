from google.adk.agents import Agent
from .tools import register_memory


memory_registration_agent = Agent(
    name="memory_registration_agent",
    model="gemini-2.5-flash",
    description="Memory Registration Agent",
    instruction="""
       You are an agent that helps in registering a memory for the patient.
       Your task is to summarize what memory user needs to add and then use the tool `register_memory` with the summarized content to register the memory.

       Respond to the user assuring their memory is safe and can be retrieved whenever they need.

       For making the response more customized use the below patient's information:
       {patient_information}
    """,
    tools=[register_memory],
    output_key="memory_addition_output",
)