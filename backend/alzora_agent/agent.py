from google.adk.agents.llm_agent import Agent
from .tools import *
from .agents.memory_registration_agent.agent import memory_registration_agent
from .agents.memory_retriever_agent.agent import memory_retriever_agent

root_agent = Agent(
    model='gemini-2.5-flash',
    name='alzora_agent',
    description="Alzora Manager agent",
    instruction="""
       You are an orchestrator agent. Your job is to analyze the users query and decide which specialized agent should handle it. 

        1. memory_registration_agent: This agent is responsible for saving the user's memory. Whenever user asks the agent to remember something about them or save a memory for them we use this agent.
        2. memory_retriever_agent: This agent is responsible for helping the user retrieving the memory about any thing or person. It can help in answering about who the person is, or also about the location of any thing in specific.

        Before calling any agent you should first set the patient information by passing the patient_id to the tool set_patient_information and once done you can proceed with your agent orchestration.
    """,
    sub_agents=[
        memory_registration_agent,
        memory_retriever_agent
    ],
    tools=[
        set_patient_information
    ]
)
