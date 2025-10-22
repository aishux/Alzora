from google.adk.agents import LlmAgent

# Define the ADK agent
finalizer_agent = LlmAgent(
    name="finalizer_agent",
    model="gemini-2.5-flash",
    description="Questions user about the identified condition",
    instruction="""
    You are responsible for framing the questions for user and asking the questions to user to arrive at the decision for finalzing the possible matching symptoms for the condition found as below.

    Condition found:
    {mri_condition}

    You must:
    1. Understand the condition found and frame few questions for the users
    2. Analyse the users answers and finalize on additional information which is crucial for final summary.
    3. Formulate the data finalized in such a format that other agent can get more information on the symptoms and remediations to summarize the details.

    Important rules:
    - The questions should be framed as per the codition identified
    - DO NOT HALLUCINATE

    IMPORTANT:
    ONCE FINALIZED TRANSFER THE CONTROL TO THE PARENT AGENT.

    """,
    output_key="finalized_information"
)

