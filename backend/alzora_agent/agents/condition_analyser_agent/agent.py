from .sub_agents.mri_detection_agent.agent import mri_detection_agent
from .sub_agents.finalizer_agent.agent import finalizer_agent
from .sub_agents.summarizer_agent.agent import summarizer_agent
from google.adk.tools.agent_tool import AgentTool

from google.adk.agents import Agent


condition_analyser_agent = Agent(
    name="condition_analyser_agent",
    model="gemini-2.5-flash",
    description="Condition Analysis Manager agent",
    instruction="""
       You are the Condition analyser and remedy recommendation Manager agent for alzheimer's responsible for orchestrating the following sub-agents:
        - `mri_detection_agent`: Detects the condition of brain from MRI scan image.
        - `summarizer_agent`: Summarizes the symptoms, clinical notes and prescriptions to the user.
        - `finalizer_agent`: A sub-agent that helps in finalizing the summary by asking user more questions.

        ### Strictly follow the Step-by-step flow:

        1. Call the mri_detection_agent and get the condition of patient's chances of alzheimer's.
        2. Go to the finalizer_agent sub-agent to finalize on more details from the user as it does Q&A with the user
        3. Finally call the summarizer_agent and get the summarized output. Then strictly present this output to the user as it is without any changes.
    """,
    sub_agents=[finalizer_agent, mri_detection_agent, summarizer_agent],
    output_key="condition_analysis_summary"
)
