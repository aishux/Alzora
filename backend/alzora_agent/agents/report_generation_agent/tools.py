from alzora_agent.setup import *
from google.adk.agents.callback_context import CallbackContext
import matplotlib.pyplot as plt
import os
import glob
import smtplib, ssl, certifi
import ssl
from email.message import EmailMessage
import reportlab
from google.adk.tools import ToolContext
from email.utils import formataddr

GAPP_PASS = os.getenv("GAPP_PASS")

def create_and_save_graph(x, y, graph_title, file_name, graph_type="line"):
    """
    Create and save a graph as PNG.
    Args:
        x (list/Series): x-axis values
        y (list/Series): y-axis values
        graph_title (str): Title of the graph
        file_name (str): Name of the file (saved as .png)
        graph_type (str): "line" or "bar"
    """
    plt.figure(figsize=(8, 5))

    if graph_type == "line":
        plt.plot(x, y, marker="o", linestyle="-")
    elif graph_type == "bar":
        plt.bar(x, y)
    else:
        raise ValueError("graph_type must be 'line' or 'bar'")

    plt.title(graph_title)
    plt.xlabel("Day")
    plt.ylabel(graph_title)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{file_name}.png")
    plt.close()


def before_agent_callback_method(callback_context: CallbackContext):
    patient_id = callback_context.state["patient_information"]["patient_id"]

    data_collection = get_bigquery_data(f"""
    SELECT
        DATE(`timestamp`) AS `day`,
        ROUND(AVG(`value_heart_rate`),2) AS `avg_heart_rate`,
        ROUND(AVG(`value_step_count`),2) AS `avg_step_count`,
        ROUND(AVG(`value_sp_o_2`),2) AS `avg_spO2_level`,
        ROUND(SUM(CAST(value_fall_flag AS INT64)), 2) AS total_fall_flag
    FROM
        `patients_vitals.patient_vitals`
    WHERE
        `value_patient_id` = {patient_id}
    GROUP BY
        `day`
    ORDER BY
        `day`
    LIMIT 7
    """)

    data_collection = data_collection.to_dataframe()

    print(data_collection)

    callback_context.state["patient_weekly_vitals_data"] = data_collection.to_dict()

    # Ensure day is sorted
    data_collection = data_collection.sort_values("day")

    # Generate graphs
    create_and_save_graph(
        data_collection["day"], data_collection["avg_heart_rate"],
        "Average Heart Rate", "avg_heart_rate", "line"
    )

    create_and_save_graph(
        data_collection["day"], data_collection["avg_spO2_level"],
        "Average spO2 levels", "avg_spO2_level", "bar"
    )

    create_and_save_graph(
        data_collection["day"], data_collection["avg_step_count"],
        "Average Step Count", "avg_step_count", "bar"
    )

    create_and_save_graph(
        data_collection["day"], data_collection["total_fall_flag"],
        "Total Fall Events", "total_fall_flag", "line"
    )

    return None


def after_agent_callback_method(callback_context: CallbackContext):
    for f in ["avg_heart_rate.png", "avg_spO2_level.png", "avg_step_count.png", "total_fall_flag.png"]:
        if os.path.exists(f):
            os.remove(f)
    return None

def send_report_mail(tool_context, pdf_file_name, patient_info):
    patient_name = patient_info["first_name"] + " " + patient_info["last_name"] 
    patient_caretaker_email = get_bigquery_data(f'''
        SELECT
            ARRAY_AGG(email) as caretaker_email
            FROM 
            `alzora_datawarehouse.caretakers`,
            UNNEST(
                ARRAY(
                SELECT CAST(TRIM(pid) AS INT64) 
                FROM UNNEST(SPLIT(REGEXP_REPLACE(patient_ids, r'[\[\]]', ''))) AS pid
                WHERE TRIM(pid) != ''
                )
            ) as patient_id
            WHERE 
            patient_id={patient_info['patient_id']}
            GROUP BY
            patient_id;
    ''')

    row = list(patient_caretaker_email)[0]
    
    patient_caretaker_email = row.caretaker_email

    matches = glob.glob(pdf_file_name)
    if matches:
        report_file_name = matches[0]
        weekly_date = "-".join(report_file_name.split(".")[0].split("-")[1:])
        subject = f"{patient_name} Weekly Report for {weekly_date}"
        body = f"""
Dear {patient_name}'s Caretaker,

Please find attached the weekly report for your loving patient {patient_name}.

Please reach out to us if you need any further help.

With ❤️ from Alzora Team
        """

        # Sender details
        sender_email = "nikhilsmankani@gmail.com"
        app_password = GAPP_PASS

        # Create email
        msg = EmailMessage()
        msg["From"] = formataddr(("Alzora Team", sender_email))
        msg["To"] = patient_caretaker_email
        msg["Subject"] = subject
        msg.set_content(body)

        # Attach PDF
        with open(report_file_name, "rb") as f:
            file_data = f.read()
            msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=report_file_name)

        # Send email
        context = ssl.create_default_context(cafile=certifi.where())
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)

        print(f"✅ Email sent to {patient_caretaker_email} with report {report_file_name}")
        os.remove(report_file_name)
    else:
        print("No match found")

def patient_python_code_execution(tool_context: ToolContext, content: dict):
    python_code = content["python_code"]
    print("Python Code: ", python_code)
    exec(python_code, {"reportlab":reportlab})
    patient_info = tool_context.state["patient_information"]
    pdf_path = f"{patient_info['patient_id']}_weekly_alzora_report-*.pdf"
    send_report_mail(tool_context, pdf_path, patient_info)
    return True