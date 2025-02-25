import time
from decoder import DatagramDecoder

def main():
    # Initialize the DatagramDecoder
    decoder = DatagramDecoder()

    # Ensure serial connection is valid
    if not decoder.ser or not decoder.ser.is_open:
        print("Failed to open serial port. Exiting...")
        return

    try:
        while True:
            decoded_data = decoder.read()  # Read from serial and process data

            if decoded_data:
                print("Decoded Data:", decoded_data)

    except KeyboardInterrupt:
        print("\nExiting program.")
    finally:
        if decoder.ser and decoder.ser.is_open:
            decoder.ser.close()

if __name__ == "__main__":
    main()