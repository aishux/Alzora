from .sub_agents.semantic_search_agent.agent import semantic_search_agent
from .sub_agents.usual_spot_agent.agent import usual_spot_search_agent

from google.adk.agents import LlmAgent


memory_retriever_agent = LlmAgent(
    name="memory_retriever_agent",
    model="gemini-2.5-flash",
    description="Memory Retriever Manager agent",
    instruction="""
       You are the Memory retriever Manager agent responsible for orchestrating the following sub-agents:
        - `semantic_search_agent`: Performs semantic search for a image or text given by the user in query.
        - `usual_spot_agent`: Performs analysis on finding the memory or query in the usual spots.

        ### Strictly follow the Step-by-step flow:
        - If the user asks query similar to "who is this person?" then use the semantic_search_agent for doing the image search and finding the information about the person in question
        - If the user asks about a thing/object's location then follow the below steps:
        - First rephrase the user query for better search. 
        - Call the semantic_search_agent to find the data from memories
        - Pass the rephrased user query to usual_spot_search_agent to get the information about the usual spots of that object/thing
        - Based on the responses you get from both the sub agents frame the detailed answer for the user which is easy to interpret.

        Make sure to give as detailed instructions as possible as your user is a alzheimer's patient.
    """,
    sub_agents=[semantic_search_agent, usual_spot_search_agent],
    output_key="retrived_memory_information"
)
