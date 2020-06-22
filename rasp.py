import bluetooth
import logging
import pickle
from skullpkt import Skullpkt
from cmd import CMD

class rasp:
    """
    RASP: Class to be run on a raspberry pi server
        RFCOMM is a reliable stream-based protocol. 
        L2CAP is a UDP like service. 
    
    We will be using RFCOMM
    """

    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='[INFO :: %(asctime)s] :: %(message)s')
        logging.info("Hello, skullpos!")
        self.uuid = "CAFE"
        self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server_sock.bind(("", bluetooth.PORT_ANY))
        self.server_sock.listen(1)
        bluetooth.advertise_service(self.server_sock, "skullpos", service_id=self.uuid,
                            service_classes=[self.uuid, bluetooth.SERIAL_PORT_CLASS],
                            profiles=[bluetooth.SERIAL_PORT_PROFILE],
                            # protocols=[bluetooth.OBEX_UUID]
                            )
        logging.info("LISTENING on RFCOMM :: %s/%d" % (bluetooth.read_local_bdaddr()[0], self.server_sock.getsockname()[1]))
        self.client_sock, self.client_info = self.server_sock.accept()
        logging.info("ACCEPTED :: %s" % self.client_info[0])

        self.mainloop()
        
    def mainloop(self):
        while True:
            data = self.client_sock.recv(4096)
            if not data:
                break
            pkt = pickle.loads(data)
            logging.info("DATA :: %s" % pkt)        

            
        

if __name__ == "__main__":
    rasp = rasp()
