from confluent_kafka import Consumer, Producer
from google.cloud import bigquery
import smtplib, ssl, certifi
import ssl
from email.message import EmailMessage
from email.utils import formataddr
import os
import json
from dotenv import load_dotenv

load_dotenv()

GAPP_PASS = os.getenv("GAPP_PASS")
bigquery_client = bigquery.Client()

def read_config():
  config = {}
  with open("client.properties") as fh:
    for line in fh:
      line = line.strip()
      if len(line) != 0 and line[0] != "#":
        parameter, value = line.strip().split('=', 1)
        config[parameter] = value.strip()
  return config

def get_bigquery_data(query):
    QUERY = (query)
    query_job = bigquery_client.query(QUERY)
    rows = query_job.result()
    return rows


def send_alert_mail(alert_details):

    patient_id = alert_details["patient_id"]

    caretakers_emails = get_bigquery_data(f'''SELECT 
    patient_id,
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
    patient_id={patient_id}
    GROUP BY
    patient_id
    ORDER BY 
    patient_id;''')

    row = list(caretakers_emails)[0]
    
    caretaker_emails = row.caretaker_email

    patient_info = get_bigquery_data(f'''SELECT first_name, last_name from `alzora_datawarehouse.patients` WHERE patient_id={row.patient_id}''')

    patient_info = list(patient_info)[0]

    print("For Patient id: ", row.patient_id, "Caretakers Emails: ", caretaker_emails, "Patient's Name: ", patient_info.first_name + " " + patient_info.last_name)

    subject = f"Your patient {patient_info.first_name} {patient_info.last_name} is out of Safe Zone!!"
    body = f"""
        Dear Caretaker,

        This alert is regarding your patient {patient_info.first_name} {patient_info.last_name}.

        They have been detected to have gone out of your configured safe zone.

        Please find the latest details below:

        Event Time: {alert_details["event_ts"]}
        GPS_Latitude: {alert_details["gps_lat"]}
        GPS_Longitude: {alert_details["gps_long"]}
        GPS_Latitude: {alert_details["gps_lat"]}
        Distance Away from Safe Zone: {alert_details["distance_meters"]} meters
        

        Please let us know or use our application if you need any further insights. 

        With ❤️ from Alzora Team
    """
    sender_email = "nikhilsmankani@gmail.com"
    app_password = GAPP_PASS

    # Create email
    msg = EmailMessage()
    msg["From"] = formataddr(("Alzora Team", sender_email))
    msg["To"] = caretaker_emails
    msg["Subject"] = subject
    msg.set_content(body)

    context = ssl.create_default_context(cafile=certifi.where())
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, app_password)
        server.send_message(msg)
    
    print("Sent Email Successfully!")


def consume(topic, config):
    # sets the consumer group ID and offset
    config["group.id"] = "alzora-alerting-1"
    config["auto.offset.reset"] = "earliest"

    # creates a new consumer instance
    consumer = Consumer(config)

    # subscribes to the specified topic
    consumer.subscribe([topic])

    try:
        while True:
            # consumer polls the topic and prints any incoming messages
            msg = consumer.poll(1.0)
            if msg is not None and msg.error() is None:
                value = msg.value().decode("utf-8")
                print(f"Consumed message from topic {topic}: value = {value:12}")
                value = json.loads(value)
                send_alert_mail({
                    "patient_id": value.get("patient_id"),
                    "event_ts": value.get("event_ts"),
                    "gps_lat": value.get("gps_lat"),
                    "gps_long": value.get("gps_long"),
                    "distance_meters": value.get("distance_meters")
                })
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

def produce(topic, config):
    # creates a new producer instance
    producer = Producer(config)

    # produces a sample message
    key = "1"
    value = json.dumps({
    "created_at": "2025-10-21T10:22:17+00:00",
    "distance_meters": 6270834.276524853,
    "event_ts": "2025-10-19T11:51:06+00:00",
    "gps_lat": 19.08686042215248,
    "gps_long": 72.87466788957467,
    "is_outside_safe_zone": True,
    "patient_id": 1,
    "safe_center_lat": 19.08593428306023,
    "safe_center_long": 12.87493471397659,
    "safe_radius_meters": 300,
    "operation": "added"
    })

    producer.produce(topic, key=key, value=value)
    print(f"Produced message to topic {topic}: key = {key:12} value = {value:12}")

    # send any outstanding or buffered messages to the Kafka broker
    producer.flush()



def main():
    config = read_config()
    topic = "safezone_alerts"
    produce(topic, config)
    consume(topic, config)

main()