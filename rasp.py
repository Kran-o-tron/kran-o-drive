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
        self.setup() # start variables and wait for connection
        self.mainloop() # enter connection loop
        
    def mainloop(self):
        while True:
            data = self.client_sock.recv(4096)
            if not data:
                break
            data = pickle.loads(data)  # cast to skull packet
            pkt = Skullpkt()
            pkt.cast(data)  # ensure pycharm detects as Skullpkt class
            logging.info("DATA :: %s" % pkt)

            # handle packet data
            for cmd in pkt.get_pkt_cmds():
                if cmd.cmd in ['height', 'pitch', 'yaw']:
                    logging.info("ATTEMPT MOVE :: %s :: %d" % (cmd.cmd, cmd.amount))
                    self.move(cmd.cmd, cmd.amount)
                elif cmd.cmd == "save":
                    logging.info("SAVING... :: height %d | pitch %d | yaw %d" % (self.pos['height'],
                                                                                 self.pos['pitch'],
                                                                                 self.pos['yaw']))
                    # create packet of a dictionary to send back
                    data_string = pickle.dumps(self.pos)
                    # send it through the socket
                    self.client_sock.send(data_string)
                    logging.info("SENT POS INFO")
                    
                elif cmd.cmd == "reset":
                    # reset all pos, move back to 0
                    pass
                elif cmd.cmd == "close":
                    # close the socket nicely, reset to 0
                    pass
    
    def move(self, axis:str, distance:int):
        # get difference between max and current
        # todo fix this!
        # move that amount
        self.pos[axis] += distance

    def setup(self):
        logging.basicConfig(level=logging.INFO, format='[INFO :: %(asctime)s] :: %(message)s')
        logging.info("Hello, skullpos!")
        self.uuid = "CAFE"
        self.pos = dict()  # used to store info on servo positions
        self.pos['height'] = 0
        self.pos['pitch'] = 0
        self.pos['yaw'] = 0
        # todo reset pos if out of wack
        
        """ bluetooth connection """
        self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server_sock.bind(("", bluetooth.PORT_ANY))
        self.server_sock.listen(1)
        bluetooth.advertise_service(self.server_sock, "skullpos", service_id=self.uuid,
                                    service_classes=[self.uuid, bluetooth.SERIAL_PORT_CLASS],
                                    profiles=[bluetooth.SERIAL_PORT_PROFILE])
        logging.info("LISTENING on RFCOMM :: %s/%d" % (bluetooth.read_local_bdaddr()[0], self.server_sock.getsockname()[1]))
        # wait for a connection!
        self.client_sock, self.client_info = self.server_sock.accept()
        logging.info("ACCEPTED :: %s" % self.client_info[0])
        

if __name__ == "__main__":
    rasp = rasp()
