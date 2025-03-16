import threading
import queue
import time
from decoder import DatagramDecoder
from db_upload import DBUpload

decoder = DatagramDecoder()
db = DBUpload()

data_queue = queue.Queue(maxsize=10000)
upload_interval = 2

def data_upload():
    while True:
        batch = []
        start_time = time.time()
        while time.time() - start_time < upload_interval:
            try:
                batch.append(data_queue.get(timeout=upload_interval))
            except queue.Empty:
                break
        if batch:
            db.upload(batch)

upload_thread = threading.Thread(target=data_upload, daemon=True)
upload_thread.start()

while True:
    data = decoder.read()
    if data:
        try:
            data_queue.put_nowait(data)
        except queue.Full:
            print("Warning: Data queue is full, dropping packet")