import serial
import time
import pty
import os
from decoder import DatagramDecoder  

def main():
    # Configure the serial connection
    serial_port = "/dev/tty.usbmodem101"  # Replace with the correct port for your board
    baud_rate = 115200
    timeout = 1  # Timeout in seconds

    try:
        # Initialize the serial connection

        ser = serial.Serial(serial_port, baud_rate, timeout=timeout)
        print(f"Connected to {serial_port} at {baud_rate} baud.")

        # Create an instance of the DatagramDecoder
        decoder = DatagramDecoder()

        # Continuously read data from the serial port
        while True:
            # Read available data from the serial port
            if ser.in_waiting > 0:
                raw_data = ser.read(ser.in_waiting)
                print(f"Raw Data Received: {raw_data}")

                for byte in raw_data:
                    if decoder.parse_byte(byte): # Call parse_byte for each byte
                        message = decoder.db.get_message_by_frame_id(decoder.datagram["id"])
                        decoded_data = message.decode(bytes(decoder.datagram['data']))
                        print("Decoded data:", decoded_data)

            time.sleep(0.1)  # Small delay to avoid excessive CPU usage

    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except KeyboardInterrupt:
        print("Exiting program.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()