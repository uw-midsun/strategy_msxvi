import serial

ser = serial.Serial("/dev/tty.usbserial-D30DPX93", 115200, timeout=1)
print(f"Serial port RX opened successfully.")

while(True):
    byte = ser.read()
    print(f"Received: {byte}")