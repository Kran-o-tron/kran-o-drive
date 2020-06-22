import sys
import bluetooth
import argparse

class mach:
    def __init__(self, bdaddr:str):
        self.bdaddr = bdaddr
        self.sock = None

        self.connect()
        self.mainloop()

    def mainloop(self):
        print("Connected. Type something...")
        while True:
            data = input()
            if not data:
                break
            self.sock.send(data.encode())

    def connect(self):
        service_matches = bluetooth.find_service(address=self.bdaddr)
        first_match = service_matches[0]
        port = first_match["port"]
        name = first_match["name"]
        host = first_match["host"].decode() 

        self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.sock.connect((host, port))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='skullpos client')
    parser.add_argument('bluetooth_addr', type=str)
    args = parser.parse_args()
    mach = mach(args.bluetooth_addr)