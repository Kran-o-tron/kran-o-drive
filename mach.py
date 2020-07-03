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
        print("==========================================================")
        print("Connected. Give a command in the format -> <cmd>::<amount>")
        print("Type ? or help for a list of commands.")
        print("==========================================================")
        while True:
            data = input(">")
            if not data:
                break
            
            cmds = data.split(" ")
            pkt = Skullpkt()
            for indiv in cmds:
                if indiv in ['reset', 'close']:
                    # handle without value
                    c = CMD(indiv)
                    pkt.add_cmd(c)
                elif indiv in ['save']: #todo regex for :: before name saved under
                    c = CMD(indiv)
                    pkt.add_cmd(c)
                    
                    # wait for save packet response 
                    
                    # save to JSON under given name
                    
                elif indiv == "?":
                    print("Valid commands...")
                    print(CMD.permitted_cmds())
                else:
                    indiv = indiv.split("::")
                    if indiv[0] in CMD.permitted_cmds():
                        try:
                            c = CMD(indiv[0], int(indiv[1]))
                            pkt.add_cmd(c)
                        except ValueError as e:
                            print("     <" + indiv[0] + ">" + "BAD COMMAND")
                    else:
                        print("     <" + indiv[0] + ">" + "BAD COMMAND")
                    
                    
            if len(pkt.get_pkt_cmds()) != 0: # only send if there are valid cmds
                data_string = pickle.dumps(pkt)
                self.sock.send(data_string) # send along the socket to the rpi

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