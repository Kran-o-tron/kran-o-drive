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


    
    

    


# import sys
# import bluetooth

# uuid = "1e0ca4ea-299d-4335-93eb-27fcfe7fa848"
# service_matches = bluetooth.find_service( uuid = uuid )

# if len(service_matches) == 0:
#     print ("couldn't find the FooBar service")
#     sys.exit(0)

# first_match = service_matches[0]
# port = first_match["port"]
# name = first_match["name"]
# host = first_match["host"]

# print ("connecting to \"%s\" on %s" % (name, host))

# sock=bluetooth.BluetoothSocket( bluetooth.RFCOMM )
# sock.connect((host, port))
# sock.send("hello!!")
# sock.close()