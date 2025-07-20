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

def main():
    parser = argparse.ArgumentParser(description="Read and decode CAN messages")
    parser.add_argument("--port", type=str, nargs='?', help="Serial port")
    args = parser.parse_args()

    if not args.port:
        args.port = input_with_completion("Enter serial port: ")

    from decoder import DatagramDecoder
    decoder = DatagramDecoder(args.port)
    if not decoder.ser or not decoder.ser.is_open:
        print("Failed to open serial port. Exiting...")
        return

    try:
        while True:
            decoded_data = decoder.read() 
            if decoded_data:
                print("Decoded Data:", decoded_data)
    except KeyboardInterrupt:
        print("\nExiting program.")
    finally:
        if decoder.ser and decoder.ser.is_open:
            decoder.ser.close()

if __name__ == "__main__":
    main()
