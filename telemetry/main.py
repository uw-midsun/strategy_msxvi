import threading

from decoder import DatagramDecoder
from db_upload import DBUpload

decoder = DatagramDecoder()
db = DBUpload

buffer = []
BUFFER_UPLOAD_SIZE = 50

while True:
    data = decoder.read()
    if data:
        buffer.append(data)
        if len(buffer) >= BUFFER_UPLOAD_SIZE:
            db.upload(buffer)

