from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import time
import random

# Configuration
url = "http://localhost:8086"
token = "token"
org = "org"
bucket = "bucket"

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

'''
Telemetry Data:
- battery_status
- battery_vt
- AFE 1
- AFE 2
- AFE 3
- cc_info
- cc_pedal
- cc_steering
- Motor_controller_vc 
- motor_velocity
- mc_status
- pd_status
'''

while True:
    #example:
    temperature = random.uniform(20.0, 25.0)
    current = random.uniform(5.0, 15.0)

    # Create data point
    point = Point("telemetry") \
        .field("temperature", temperature) \
        .field("current", current) \
        .time(time.time_ns())

    write_api.write(bucket=bucket, org=org, record=point)

    print(f"Data written: temperature={temperature}, current={current}")
    time.sleep(1)
