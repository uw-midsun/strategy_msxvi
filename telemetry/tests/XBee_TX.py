import serial

ser = serial.Serial("/dev/tty.usbserial-DA005UE0", 115200, timeout=1)
print(f"Serial port TX opened successfully.")

values = bytearray([0, 1, 2, 3, 4, 5, 6])
ser.write(values)