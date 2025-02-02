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
        self.ser = self._init_serial(serial_port, baud_rate, timeout)
        self.db = self._init_dbc(dbc_path)
        self.message_state = State.SOM
        self.buffer = []
        self.datagram = None

    def _init_serial(self, port, baud_rate, timeout):
        ser = serial.Serial(port, baud_rate, timeout=timeout)
        print(f"Serial port {port} opened successfully.")
        return ser

    def _init_dbc(self, dbc_path):
        return cantools.database.load_file(dbc_path)

    def read(self):
        while self.ser.in_waiting > 0:
            byte = self.ser.read(1)[0]  # Read one byte at a time

            if self.parse_byte(byte):  # If a complete message is detected
                return self.decode_datagram()
        
        return None

    def decode_datagram(self):
        
        if not self.datagram:
            return None

        message = self.db.get_message_by_frame_id(self.datagram["id"])
        if not message:
            print(f"Unknown message ID: {self.datagram['id']}")
            return None

        decoded_data = message.decode(bytes(self.datagram["data"]))
        return self._format_decoded_message(message, decoded_data)

    def _format_decoded_message(self, message, decoded_data):
        formatted_data = {"message": message.name, "id": self.datagram["id"], "data": {}}

        for signal_name, value in decoded_data.items():
            formatted_data["data"][signal_name] = value

        return formatted_data

    def is_valid_id(self, id):
        return self.db.get_message_by_frame_id(id) is not None

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
            if self.datagram["dlc"] <= 8:  
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