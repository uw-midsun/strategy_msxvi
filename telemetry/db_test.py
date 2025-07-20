import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../db")))

from db_upload import DBUpload
from decoder import DatagramDecoder

decoder = DatagramDecoder(test=True)
db = DBUpload()

sample_data = [0xAA, 0x00, 0x01, 0x07, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0xBB]

for byte in sample_data:
    msg = decoder.read_test(byte)
    if msg:
        db.upload([msg])