import os
import pty
import cantools
import serial

class State:
    SOM = "SOM"
    ID = "ID"
    DLC = "DLC"
    DATA = "DATA"
    EOM = "EOM"
    VALID = "VALID"

class DatagramDecoder:
    def __init__(self):
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

        self.init_serial()
        self.init_dbc()

    def init_serial(self):
        self.master, self.slave = pty.openpty()
        self.slave_name = os.ttyname(self.slave)
        self.slave_serial = serial.Serial(self.slave_name) #args?

    def init_dbc(self):
        dbc_path = "system_can.dbc"
        self.db = cantools.database.load_file(dbc_path)

    def write(self, packet):
        self.slave_serial.write(bytes(packet))

    def read(self):
        recv = os.read(self.master, 1000)
        if self.parse_byte(recv):
            message = self.db.get_message_by_frame_id(self.datagram['id'])
            decoded_data = message.decode(self.datagram['data'])
            return decoded_data

    def convert_AFE_msg(self, message, raw_AFE_decoded_data):
        msg_id = raw_AFE_decoded_data["id"]
        AFE_num = message.name[0:4]
        AFE_temp_name = AFE_num+"temp"+str(msg_id)
        AFE_v1_name = AFE_num+"v"+str(1+(3*msg_id))
        AFE_v2_name = AFE_num+"v"+str(2+(3*msg_id))
        AFE_v3_name = AFE_num+"v"+str(3+(3*msg_id))
        AFE_message = {"id": msg_id, AFE_temp_name: raw_AFE_decoded_data["temp"], AFE_v1_name: raw_AFE_decoded_data["v1"], AFE_v2_name: raw_AFE_decoded_data["v2"], AFE_v3_name: raw_AFE_decoded_data["v3"]}
        return AFE_message    
    
    def convert_bms_fault(self, fault_bitset):
        fault_msg = {"BMS_FAULT_OVERVOLTAGE": 0,
            "BMS_FAULT_UNBALANCE": 0, 
            "BMS_FAULT_OVERTEMP_AMBIENT": 0,
            "BMS_FAULT_COMMS_LOSS_AFE": 0,
            "BMS_FAULT_COMMS_LOSS_CURR_SENSE": 0,
            "BMS_FAULT_OVERTEMP_CELL": 0,
            "BMS_FAULT_OVERCURRENT": 0,
            "BMS_FAULT_UNDERVOLTAGE": 0,
            "BMS_FAULT_KILLSWITCH": 0,
            "BMS_FAULT_RELAY_CLOSE_FAILED": 0,
            "BMS_FAULT_DISCONNECTED": 0}
        for i in range(len(self.BMS_FAULTS)):
            if fault_bitset & (1 << i):
                fault_msg[self.BMS_FAULTS[i]] = 1
        return fault_msg

    def read_test(self, byte):
        if self.parse_byte(byte):
            message = self.db.get_message_by_frame_id(self.datagram['id'])
            decoded_data = message.decode(bytes(self.datagram['data']))
            if message.name in self.AFE_MSGS:
                decoded_data = self.convert_AFE_msg(message, decoded_data)
            if message.name == "battery_status":
                decoded_data = self.convert_bms_fault(decoded_data["fault"])
            if message.name == "pd_status":
                pass
            return decoded_data

    def is_valid_id(self, id):
        try:
            self.db.get_message_by_frame_id(id)
            return True
        except KeyError:
            return False

    def reset_buffer_and_datagram(self):
        self.buffer = []
        self.datagram = None

    def handle_id(self):
        if len(self.buffer) == 4:
            message_id = int.from_bytes(self.buffer, byteorder='big')
            if self.is_valid_id(message_id):
                self.datagram = {"id": message_id}
                self.buffer = []
                self.message_state = State.DLC
            else:
                self.message_state = State.SOM

    def handle_dlc(self):
        if self.datagram["dlc"] <= 9:
            self.datagram["data"] = []
            self.message_state = State.DATA
        else:
            self.message_state = State.SOM

    def handle_eom(self, byte):
        if byte == 0xBB:
            self.message_state = State.VALID
        else:
            self.message_state = State.SOM

    def parse_byte(self, byte):
        if self.message_state == State.SOM or self.message_state == State.VALID:
            self.reset_buffer_and_datagram()
            if byte == 0xAA:
                self.message_state = State.ID
        elif self.message_state == State.ID:
            self.buffer.append(byte)
            self.handle_id()
        elif self.message_state == State.DLC:
            self.datagram["dlc"] = byte
            self.handle_dlc()
        elif self.message_state == State.DATA:
            self.buffer.append(byte)
            if len(self.buffer) == self.datagram["dlc"]:
                self.datagram["data"] = self.buffer
                self.message_state = State.EOM
        elif self.message_state == State.EOM:
            self.handle_eom(byte)
        return self.message_state == State.VALID
