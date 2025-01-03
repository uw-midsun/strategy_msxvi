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
            message = self.db.get_message_by_frame_id(self.datagram["id"])
            decoded_data = message.decode(self.datagram['data'])
            print(decoded_data)
            #upload decoded_data using PostgreSQL

    def read_test(self, byte):
        if self.parse_byte(byte):
            message = self.db.get_message_by_frame_id(self.datagram["id"])
            decoded_data = message.decode(bytes(self.datagram['data']))
            print(decoded_data)

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
