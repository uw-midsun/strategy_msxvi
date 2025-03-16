import cantools
import serial
import struct

class State:
    SOM = "SOM"
    ID = "ID"
    DLC = "DLC"
    DATA = "DATA"
    EOM = "EOM"
    VALID = "VALID"

class DatagramDecoder:
    def __init__(self, serial_port="/dev/tty.usbserial-D30DPX93", baud_rate=115200, timeout=1, dbc_path="system_can.dbc", test=False):
        #REPLACE serial_port WITH YOUR COMPUTER's SERIAL PORT. TODO: make this process easier
        self.dbc = self.init_dbc(dbc_path)
        if not test:
            self.ser = self.init_serial(serial_port, baud_rate, timeout)

        self.message_state = State.SOM
        self.buffer = []
        self.datagram = None

        self.AFE_MSGS = ["AFE1_status", "AFE2_status", "AFE3_status"]

        self.BMS_FAULTS = [
            "BMS_FAULT_OVERVOLTAGE",
            "BMS_FAULT_UNBALANCE", 
            "BMS_FAULT_OVERTEMP_AMBIENT",
            "BMS_FAULT_COMMS_LOSS_AFE",
            "BMS_FAULT_COMMS_LOSS_CURR_SENSE",
            "BMS_FAULT_OVERTEMP_CELL",
            "BMS_FAULT_OVERCURRENT",
            "BMS_FAULT_UNDERVOLTAGE",
            "BMS_FAULT_KILLSWITCH",
            "BMS_FAULT_RELAY_CLOSE_FAILED",
            "BMS_FAULT_DISCONNECTED"
        ]

        self.PD_FAULTS = [
            "EE_PD_STATUS_FAULT_BITSET_AUX_FAULT_BIT",
            "EE_PD_STATUS_FAULT_BITSET_DCDC_FAULT_BIT",
            "NUM_EE_PD_STATUS_FAULT_BITSET_BIT",
        ]

    def init_serial(self, port, baud_rate, timeout):
        ser = serial.Serial(port, baud_rate, timeout=timeout)
        print(f"Serial port {port} opened successfully.")
        return ser

    def init_dbc(self, dbc_path):
        return cantools.database.load_file(dbc_path)
    
    def convert_AFE_msg(self, message, raw_AFE_decoded_data):
        msg_id = raw_AFE_decoded_data["id"]
        AFE_num = message.name[0:4]
        AFE_temp_name = AFE_num+"temp"+str(msg_id)
        AFE_v1_name = AFE_num+"v"+str(1+(3*msg_id))
        AFE_v2_name = AFE_num+"v"+str(2+(3*msg_id))
        AFE_v3_name = AFE_num+"v"+str(3+(3*msg_id))
        AFE_message = {AFE_temp_name: raw_AFE_decoded_data["temp"], AFE_v1_name: raw_AFE_decoded_data["v1"], AFE_v2_name: raw_AFE_decoded_data["v2"], AFE_v3_name: raw_AFE_decoded_data["v3"]}
        return AFE_message    

    def convert_fault(self, fault_bitset, fault_list):
        return {fault: int(bool(fault_bitset & (1 << i))) for i, fault in enumerate(fault_list)}

    def convert_BMS_fault(self, decoded_data):
        bms_msg = self.convert_fault(decoded_data["fault"], self.BMS_FAULTS)
        bms_msg["aux_batt_v"] = decoded_data["aux_batt_v"]
        bms_msg["afe_status"] = decoded_data["afe_status"]
        return bms_msg

    def convert_PD_fault(self, decoded_data):
        pd_msg = self.convert_fault(decoded_data["fault_bitset"], self.PD_FAULTS)
        pd_msg["power_state"] = decoded_data["power_state"]
        pd_msg["bps_persist"] = decoded_data["bps_persist"]
        return pd_msg

    def int_to_float(self, value):
        return struct.unpack('<f', value.to_bytes(4, byteorder='little'))[0]

    def convert_pedal_throttle(self, decoded_data):
        return {
            "throttle_output": self.int_to_float(decoded_data["throttle_output"]),
            "brake_output": decoded_data["brake_output"],
        }

    def read(self):
        while self.ser.in_waiting > 0:
            byte = self.ser.read(1)[0]
            if self.parse_byte(byte):
                return self.decode_datagram()
        return None
    
    def read_test(self, byte):
        if self.parse_byte(byte):
            return self.decode_datagram()
        return None

    def decode_datagram(self):
        message = self.dbc.get_message_by_frame_id(self.datagram["id"])
        decoded_data = message.decode(bytes(self.datagram["data"]))
        if message.name in self.AFE_MSGS:
            decoded_data = self.convert_AFE_msg(message, decoded_data)
        if message.name == "battery_status":
            decoded_data = self.convert_BMS_fault(decoded_data)
        if message.name == "pd_status":
            decoded_data = self.convert_PD_fault(decoded_data)
        if message.name == "cc_pedal":
            decoded_data = self.convert_pedal_throttle(decoded_data)
        return decoded_data

    def is_valid_id(self, id):
        try:
            return self.dbc.get_message_by_frame_id(id) is not None
        except:
            print(f"Invalid ID: {id}")
            return False 

    def _reset_buffer(self):
        self.buffer = []
        self.datagram = None
        self.message_state = State.SOM  

    def parse_byte(self, byte):
        if self.message_state in [State.SOM, State.VALID]:
            self._reset_buffer()
            if byte == 0xAA:
                self.message_state = State.ID
        elif self.message_state == State.ID:
            self.buffer.append(byte)
            if len(self.buffer) == 2:
                message_id = int.from_bytes(self.buffer, byteorder="big")
                if self.is_valid_id(message_id):
                    self.datagram = {"id": message_id}
                    self.buffer = []
                    self.message_state = State.DLC
                else:
                    self.message_state = State.SOM  
        elif self.message_state == State.DLC:
            self.datagram["dlc"] = byte
            if self.datagram["dlc"] <= 9:  
                self.datagram["data"] = []
                self.message_state = State.DATA
            else:
                self.message_state = State.SOM  
        elif self.message_state == State.DATA:
            self.buffer.append(byte)
            if len(self.buffer) == self.datagram["dlc"]:
                self.datagram["data"] = self.buffer
                self.message_state = State.EOM
        elif self.message_state == State.EOM:
            if byte == 0xBB:
                self.message_state = State.VALID
            else:
                self.message_state = State.SOM  
        return self.message_state == State.VALID