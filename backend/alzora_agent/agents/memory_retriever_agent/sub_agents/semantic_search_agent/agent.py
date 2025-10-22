from google.adk.agents import Agent
from .tools import search_memory


semantic_search_agent = Agent(
    name="semantic_search_agent",
    model="gemini-2.5-flash",
    description="Semantic Search Agent",
    instruction="""
       You are an agent that performs semantic search for finding the memories related to user query.
       
       You have to strictly use the tool `search_memory` with the user query without any thought. 
       This tool is also capable of searching memory using image.

       Once you have the response from the tool summarize the `text_content` in complete detail.

       Make sure to give as detailed instructions as possible as your user is a alzheimer's patient.

       IMPORTANT:
       If you can't find the thing mentioned by user then TRANSFER THE CONTROL TO THE PARENT AGENT.

       For making the response more customized use the below patient's information:
       {patient_information}
    """,
    tools=[search_memory],
    output_key="semantic_search_agent_output",
)