import bluetooth
import logging
import pickle
from skullpkt import Skullpkt
from cmd import CMD
import sys
from socket import error as SocketError
import errno


class rasp:
    """
    RASP: Class to be run on a raspberry pi server
        RFCOMM is a reliable stream-based protocol. 
        L2CAP is a UDP like service. 
    
    We will be using RFCOMM.
    """

    def __init__(self):
        self.setup()  # start variables and wait for connection
        self.mainloop()  # enter connection loop

    def mainloop(self):
        while True:
            try:
                data = self.sock.recv(4096)
            except SocketError as e:
                if e.errno != errno.ECONNRESET:
                    raise  # Not error we are looking for
                self.sock.close()
                logging.info("SHUTTING DOWN...")
                sys.exit(0)

            if not data:
                break
            data = pickle.loads(data)  # cast to skull packet
            pkt = Skullpkt()
            pkt.cast(data)  # ensure pycharm detects as Skullpkt class
            logging.info("DATA :: %s" % pkt)

            # handle packet data
            for cmd in pkt.get_pkt_cmds():
                if cmd.cmd in ['height', 'pitch', 'yaw', 'roll', 'width']:
                    logging.info("ATTEMPT MOVE :: %s :: %d" % (cmd.cmd, cmd.amount))
                    self.move(cmd.cmd, cmd.amount)
                    
                elif cmd.cmd == "save":
                    logging.info(f"SAVING...")
                    # create packet of a dictionary to send back
                    data_string = pickle.dumps(self.pos)
                    # send it through the socket
                    self.sock.send(data_string)
                    logging.info("SENT POS INFO")
                    
                elif cmd.cmd == "load":
                    # move to pos
                    logging.info(f"MOVING TO :: {cmd.pos}")
                    # height
                    height_diff = cmd.pos["height"] - self.pos["height"]
                    self.move(axis="height", distance=height_diff)
                    # width
                    width_diff = cmd.pos["width"] - self.pos["width"]
                    self.move(axis="width", distance=width_diff)                 
                    # pitch
                    pitch_diff = cmd.pos["pitch"] - self.pos["pitch"]
                    self.move(axis="pitch", distance=pitch_diff)
                    # yaw
                    yaw_diff = cmd.pos["yaw"] - self.pos["yaw"] 
                    self.move(axis="yaw", distance=yaw_diff)
                    # roll
                    roll_diff = cmd.pos["roll"] - self.pos["roll"]
                    self.move(axis="roll", distance=roll_diff)
                    
                elif cmd.cmd == "reset":
                    # reset all pos, move back to 0
                    logging.info("RESET POS TO ORIGIN")
                    self.reset()
                    pass  # todo move 

                elif cmd.cmd == "close":
                    # close the socket nicely, reset to 0
                    self.reset()
                    self.close()

    def close(self):
        self.sock.close()
        sys.exit(0)

    def reset(self):
        self.pos['height'] = 0
        self.pos['pitch'] = 0
        self.pos['yaw'] = 0
        self.pos['roll'] = 0
        self.pos['width'] = 0
        # todo move

        
    def move(self, axis: str, distance: int):
        # move that amount
        logging.info(f"MOVING {axis} -> {distance}")
        self.pos[axis] += distance
        logging.info(f"ARRIVED {axis} :: {self.pos[axis]}")
        # todo move the motorkit


    def setup(self):
        logging.basicConfig(level=logging.INFO, format='[INFO :: %(asctime)s] :: %(message)s')
        logging.info("Hello, skullpos!")
        self.uuid = "CAFE"
        self.pos = dict()  # used to store info on servo positions
        self.pos['height'] = 0
        self.pos['pitch'] = 0
        self.pos['yaw'] = 0
        self.pos['roll'] = 0
        self.pos['width'] = 0
        # todo reset pos if out of wack

        """ bluetooth connection """
        self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server_sock.bind(("", bluetooth.PORT_ANY))
        self.server_sock.listen(1)
        bluetooth.advertise_service(self.server_sock, "skullpos", service_id=self.uuid,
                                    service_classes=[self.uuid, bluetooth.SERIAL_PORT_CLASS],
                                    profiles=[bluetooth.SERIAL_PORT_PROFILE])
        logging.info(f"LISTENING on RFCOMM :: {bluetooth.read_local_bdaddr()[0]}")
        # wait for a connection!
        self.sock, self.client_info = self.server_sock.accept()
        logging.info("ACCEPTED :: %s" % self.client_info[0])


if __name__ == "__main__":
    rasp = rasp()
