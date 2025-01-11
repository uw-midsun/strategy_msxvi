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

class DBUpload:
    def upload(self, buffer):
        point = Point("telemetry")
        for data in buffer:
            for key, value in data.items():
                point = point.field(key, value)
        write_api.write(bucket=bucket, org=org, record=point)
        print(data)
        time.sleep(1)

'''
pedal freq every 20ms
everything else 200ms

assume every 200ms

Set baud rate to 115200b/s

Telemetry Data (total = 80 bytes, 640 bits):
- battery_status (7 bytes)
    - fault
    - fault value
    - aux_battery_v
    - afe_status
- battery_vt (8 bytes)
    - voltage
    - current
    - temperature
    - batt_perc
- AFE 1 (8 bytes)
    - id
    - temp
    - v1
    - v2
    - v3
- AFE 2 (8 bytes)
    - id
    - temp
    - v1
    - v2
    - v3
- AFE 3 (8 bytes)
    - id
    - temp
    - v1
    - v2
    - v3
- cc_info (8 bytes)
    - target velocity
    - drive state
    - cruise_control
    - regen_breaking
    - hazard_enabled
- cc_pedal (5 bytes)
    - throttle_output
    - brake_output
- cc_steering (2 bytes)
    - input_cc
    - input_lights
- Motor_controller_vc (8 bytes)
    - mc_voltage_l
    - mc_current_l
    - mc_voltage_r
    - mc_current_r
- motor_velocity (5 bytes)
    - velocity_l
    - velocity_r
    - brakes_enabled
- mc_status (7 bytes)
    - limit_bitset_l
    - error_bitset_l
    - limit_bitset_r
    - error_bitset_r
    - board_fault_bitset
    - overtemp_bitset
    - precharge_status
- pd_status (6 bytes)
    - power_state
    - fault_bitset
    - bps_persist
    - bps_persist_val
'''
