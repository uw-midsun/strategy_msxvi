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
    def __init__(self, serial_port="/dev/tty.usbmodem1101", baud_rate=115200, timeout=1, dbc_path="system_can.dbc"):
        #REPLACE serial_port WITH YOUR COMPUTER's SERIAL PORT
        self.ser = self.init_serial(serial_port, baud_rate, timeout)
        self.dbc = self.init_dbc(dbc_path)
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
        self.PD_FAULTS = self.BMS_FAULTS + [
            "BMS_FAULT_LOW_PRIORITY",
            "BMS_FAULT_HIGH_PRIORITY"
        ]

        self.init_serial()
        self.init_dbc()

    def init_serial(self):
        self.master, self.slave = pty.openpty()
        self.slave_name = os.ttyname(self.slave)
        self.slave_serial = serial.Serial(self.slave_name)

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
        AFE_message = {"id": msg_id, AFE_temp_name: raw_AFE_decoded_data["temp"], AFE_v1_name: raw_AFE_decoded_data["v1"], AFE_v2_name: raw_AFE_decoded_data["v2"], AFE_v3_name: raw_AFE_decoded_data["v3"]}
        return AFE_message    


    def convert_fault(self, fault_bitset, fault_list):
        return {fault: int(bool(fault_bitset & (1 << i))) for i, fault in enumerate(fault_list)}
    

    def convert_bms_fault(self, fault_bitset):
        return self.convert_fault(fault_bitset, self.BMS_FAULTS)

    def convert_pd_fault(self, fault_bitset):
        return self.convert_fault(fault_bitset, self.PD_FAULTS)


    def read(self):
        while self.ser.in_waiting > 0:
            byte = self.ser.read(1)[0]  # Read one byte at a time

            if self.parse_byte(byte):  # If a complete message is detected
                return self.decode_datagram()
        
        return None
    
    def read_test(self, byte):
        if self.parse_byte(byte):
            message = self.dbc.get_message_by_frame_id(self.datagram['id'])
            decoded_data = message.decode(bytes(self.datagram['data']))
            if message.name in self.AFE_MSGS:
                decoded_data = self.convert_AFE_msg(message, decoded_data)
            if message.name == "battery_status":
                decoded_data = self.convert_bms_fault(decoded_data["fault"])
            if message.name == "pd_status":
                decoded_data = self.convert_pd_fault(decoded_data["fault"])
            return decoded_data

    def decode_datagram(self):
        
        if not self.datagram:
            return None

        message = self.dbc.get_message_by_frame_id(self.datagram["id"])
        if not message:
            print(f"Unknown message ID: {self.datagram['id']}")
            return None

        decoded_data = message.decode(bytes(self.datagram["data"]))
        if message.name in self.AFE_MSGS:
            decoded_data = self.convert_AFE_msg(message, decoded_data)
        if message.name == "battery_status":
            decoded_data = self.convert_bms_fault(decoded_data["fault"])
        if message.name == "pd_status":
            pass
        return self._format_decoded_message(message, decoded_data)

    def _format_decoded_message(self, message, decoded_data):
        formatted_data = {"message": message.name, "id": self.datagram["id"], "data": {}}

        for signal_name, value in decoded_data.items():
            formatted_data["data"][signal_name] = value

        return formatted_data

    def is_valid_id(self, id):
        return self.dbc.get_message_by_frame_id(id) is not None

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
            if len(self.buffer) == 4:
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