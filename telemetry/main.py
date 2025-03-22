import sys
import os

# Add the parent directory (telemetry) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../db")))

import threading
import queue
import time
from decoder import DatagramDecoder
from db_upload import DBUpload
import argparse
import glob
import readline

def available_ports():
    return [port for port in glob.glob('/dev/tty.*')]

def port_completer(text, state):
    options = available_ports()
    if state < len(options):
        return options[state]
    return None

def input_with_completion(prompt: str) -> str:
    readline.set_completer_delims(' \t\n')
    readline.set_completer(port_completer)
    readline.parse_and_bind("tab: menu-complete")
    return input(prompt)

parser = argparse.ArgumentParser(description="Read and decode CAN messages")
parser.add_argument("--port", type=str, nargs='?', help="Serial port")
args = parser.parse_args()
# check for port argument if provided

# if not provided, ask for port, with tab completion to cycle between ports
if not args.port:
    args.port = input_with_completion("Enter serial port: ")

# initialize db and decoder with given port
decoder = DatagramDecoder(args.port)
db = DBUpload()

data_queue = queue.Queue(maxsize=5000)
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
        print(f"Decoded Data: {data}")
        try:
            data_queue.put_nowait(data)
        except queue.Full:
            print("Warning: Data queue is full, dropping packet")
