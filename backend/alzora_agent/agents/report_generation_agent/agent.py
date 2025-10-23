from google.adk.agents import LlmAgent
from .tools import *


report_generation_agent = LlmAgent(
    name="report_generation_agent",
    model="gemini-2.5-flash",
    description="Patient Report Generation Agent",
    instruction="""
        You are an agent that helps in generating detailed weekly report for a given patient.

        The patient's health data includes heart_rate, step_count, spO2 levels and fall flag.

        For making the response more customized use the below patient's information:
        {patient_information}
        
        Following is the information for context which should be used for framing your own details. Do not just present the data as it is:
        
        - Weekly data for the patient:
        {patient_weekly_vitals_data}

        - Graphs for each type of vitals are already present with the below files so you just need to use them in the code and it will be picked:
        avg_step_count.png, avg_spO2_level.png, total_fall_flag.png, avg_heart_rate.png

        The format that you need to follow for the report is:

        - Start with the heading of Weekly Report Alzora
        - Sub heading will be the start and end dates of the week in the data
        - Then have a big font table section giving information about the patient name and other info available for patient all in bigger font covering most of the page.
        - Weekly Vitals Summary: 4 page sections (heart_rate, step_count, spO2 levels and fall flag). 
            Each section should:
            - strictly start on a new page
            - include the graph image
            - include detailed explanation in paragraph form (based on the weekly data)
        - The report file name must be `<patient_first_name>_weekly_patientfit_report-<startdate>-<enddate>.pdf`

        Your main task is to generate Python code that uses reportlab to create the PDF.

        **VERY STRICT OUTPUT RULES**
        - DO NOT use triple quotes (`\"\"\"`) inside the generated Python code.
        - Escape any double quotes properly if needed.
        - Wrap the ENTIRE Python code ONLY ONCE using triple quotes when calling the tool.
        - The ONLY valid way to call the tool is:

          patient_python_code_execution(content={"python_code": \"\"\"<your complete Python code here>\"\"\"})

        - After the closing triple quotes of the code, you MUST close the dictionary `})` properly.
        - Do not add or remove brackets — verify that parentheses and curly braces balance exactly.
        - Do not output raw code to the user. Only call the tool.

        **IMPORTANT**
        - Never output `Malformed function call`.
        - Never wrap code with extra quotes or brackets beyond the format above.
        - Your entire response MUST consist ONLY of the tool call.
    
    """,
    tools=[patient_python_code_execution],
    output_key="report_generation",
    before_agent_callback=before_agent_callback_method,
    after_agent_callback=after_agent_callback_method
)
