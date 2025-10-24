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

  lst = [
    '60002,device_2022484408,2025-10-17 00:05:00+00:00,64,97.4,19.08686042215248,72.87466788957467,75,False,61',
    '60002,device_2022484408,2025-10-18 23:48:00+00:00,83,97.1,19.096343822352335,72.89005214265876,120,False,69',
    '60002,device_2022484408,2025-10-19 16:17:00+00:00,70,97.1,19.09777613470503,72.89004081425826,500,True,76',
    '60002,device_2022484408,2025-10-20 05:31:00+00:00,68,81.6,19.09013856682481,72.8798859612496,414,False,90',
    '60002,device_2022484408,2025-10-21 05:09:00+00:00,65,96.2,19.096146221305004,72.87733463114213,1500,True,72',
    '60002,device_2022484408,2025-10-22 00:56:00+00:00,59,96.3,19.083011313040515,72.89199589762022,200,False,61',
    '60002,device_2022484408,2025-10-23 11:29:00+00:00,98,98.1,19.086492636026998,72.88933375703684,878,False,98',
  ]

  # produces a sample message
  # key = "60002"
  # for val in lst:
  #   val = val.split(",")
  #   value = json.dumps({"patient_id":val[0], "device_id": "device_2022484408","timestamp":val[2],"heart_rate":val[3],"spO2":val[4],"gps_lat":val[5],"gps_long":val[6],"step_count":val[7],"fall_flag":val[8],
  #   "battery_level":val[9]})

  #   producer.produce(topic, key=key, value=value)
  #   print(f"Produced message to topic {topic}: key = {key:12} value = {value:12}")

  # send any outstanding or buffered messages to the Kafka broker

  key = "60002"
  value = json.dumps({"patient_id":60002, "device_id": "device_2022484408","timestamp":"2025-10-24 00:05:00+00:00","heart_rate":72,"spO2":87.4,"gps_lat":15.08686042215248,"gps_long":89.87466788957467,"step_count":7,"fall_flag":False,
  "battery_level":61})

  producer.produce(topic, key=key, value=value)

  producer.flush()

def main():
  config = read_config()
  topic = "patient_vitals"

  produce(topic, config)


main()