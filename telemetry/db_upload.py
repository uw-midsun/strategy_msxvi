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
    - fault
    - fault value
    - aux_battery_v
    - afe_status
- battery_vt
    - voltage
    - current
    - temperature
    - batt_perc
- AFE 1
    - id
    - temp
    - v1
    - v2
    - v3
- AFE 2
    - id
    - temp
    - v1
    - v2
    - v3
- AFE 3
    - id
    - temp
    - v1
    - v2
    - v3
- cc_info
    - target velocity
    - drive state
    - cruise_control
    - regen_breaking
    - hazard_enabled
- cc_pedal
    - throttle_output
    - brake_output
- cc_steering
    - input_cc
    - input_lights
- Motor_controller_vc
    - mc_voltage_l
    - mc_current_l
    - mc_voltage_r
    - mc_current_r
- motor_velocity
    - velocity_l
    - velocity_r
    - brakes_enabled
- mc_status
    - limit_bitset_l
    - error_bitset_l
    - limit_bitset_r
    - error_bitset_r
    - board_fault_bitset
    - overtemp_bitset
    - precharge_status
- pd_status
    - power_state
    - fault_bitset
    - bps_persist
    - bps_persist_val
'''

while True:
    #example:


    # Create data point
    point = Point("telemetry") \
        .field("key", value) \
        .field("key", value) \
        .time(time.time_ns())

    write_api.write(bucket=bucket, org=org, record=point)

    print(f"Data written: temperature={temperature}, current={current}")
    time.sleep(1)
