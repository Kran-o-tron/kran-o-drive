import sys
import bluetooth
import argparse
import pickle
from skullpkt import Skullpkt
from cmd import CMD

class mach:
    def __init__(self, bdaddr:str):
        self.bdaddr = bdaddr
        self.sock = None

        self.connect()
        self.mainloop()

    def mainloop(self):
        print("Connected. Give a command in the format -> <cmd>::<amount>")
        while True:
            data = input()
            if not data:
                break

            cmds = data.split(" ")
            pkt = Skullpkt()
            print(cmds)
            for indiv in cmds:
                indiv = indiv.split("::")
                print(indiv)
                c = CMD(indiv[0], int(indiv[1]))
                pkt.add_cmd(c)
            data_string = pickle.dumps(pkt)
            self.sock.send(data_string)

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