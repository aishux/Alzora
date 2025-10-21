from confluent_kafka import Producer
import json

def read_config():
  # reads the client configuration from client.properties
  # and returns it as a key-value map
  config = {}
  with open("client.properties") as fh:
    for line in fh:
      line = line.strip()
      if len(line) != 0 and line[0] != "#":
        parameter, value = line.strip().split('=', 1)
        config[parameter] = value.strip()
  return config

def produce(topic, config):
  # creates a new producer instance
  producer = Producer(config)

  # produces a sample message
  key = "2"
  value = json.dumps({"patient_id":2, "device_id": "device_2022484408","timestamp":"2025-10-20 00:05:00+00:00","heart_rate":72,"spO2":87.4,"gps_lat":19.08686042215248,"gps_long":72.87466788957467,"step_count":7,"fall_flag":False,
  "battery_level":61})

  producer.produce(topic, key=key, value=value)
  print(f"Produced message to topic {topic}: key = {key:12} value = {value:12}")

  # send any outstanding or buffered messages to the Kafka broker
  producer.flush()

def main():
  config = read_config()
  topic = "patient_vitals"

  produce(topic, config)


main()