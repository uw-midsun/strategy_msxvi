import time
from db.connect import connect_to_db

class DBUpload:
    def __init__(self):
        self.connection = connect_to_db()
        self.cursor = self.connection.cursor()
        self.init_table()

    def init_table(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_name VARCHAR(50),
                    value INTEGER 
                );
            """)
            self.connection.commit()
        except Exception as e:
            print(f"Error creating table: {e}")

    def upload(self, buffer):
        try:
            for data in buffer:
                for key, value in data.items():
                    self.cursor.execute("""
                        INSERT INTO telemetry (message_name, value)
                        VALUES (%s, %s)
                    """, (key, int(value)))
            self.connection.commit()
            print("Data uploaded successfully")
            time.sleep(1)
        except Exception as e:
            print(f"Error uploading data: {e}")
            self.connection.rollback()

'''
assume every 200ms
(pedal freq every 20ms
everything else 200ms)

Set baud rate to 115200b/s

Telemetry Data (total = 74 bytes, 592 bits):
- battery_status (7 bytes)  bms-carrier/inc/bms.h
    - fault (Bitset)
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
(Each AFE will send data 4 times (id: 0-3). Each id does 3 cells to make up the voltage of cell 1-12.
the temp will be for 4 cells so temp of id 0-2 are valid temperatures, the id 3 will be a garbage value)
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
    - limit_bitset_l no
    - error_bitset_l no
    - limit_bitset_r no
    - error_bitset_r no
    - board_fault_bitset no
    - overtemp_bitset no
    - precharge_status
- pd_status (6 bytes)
    - power_state
    - fault_bitset (Bitset)
    - bps_persist
    - bps_persist_val
'''
