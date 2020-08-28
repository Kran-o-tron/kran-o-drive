import errno
import pickle
import sys
from socket import error as socket_error
import bluetooth
import logging
import time
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper

from skullpkt import Skullpkt


class Rasp:
    """Class to be run on a raspberry pi server

    Handles the logic for receiving info from host and controlling devices over
    GPIO.
    """

    def __init__(self, demo: bool):
        self.uuid = None
        self.pos = None
        self.limits = None
        self.width: MotorKit = None
        self.pitch_yaw: MotorKit = None
        self.roll: MotorKit = None
        self.width_motor: MotorKit = None
        self.height_motors: MotorKit = None
        self.sock = None
        self.client_info = None
        self.server_sock = None

        self.setup()  # start variables and wait for connection
        if not demo:
            self.bluetooth_setup()
            self.mainloop()  # enter connection loop

    def mainloop(self):
        """Main execution loop for Mach. Waits for commands and executes their
        corresponding logic.
        """
        while True:
            try:
                data = self.sock.recv(4096)
            except socket_error as e:
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
                if cmd.action in ['pitch', 'yaw', 'roll']:
                    logging.info(
                        "ATTEMPT MOVE :: %s :: %d" % (cmd.action, cmd.amount))
                    self.plan_rotate(cmd.action, cmd.amount)
                elif cmd.action in ['height', 'width']:
                    self.plan_translate(cmd.action, cmd.amount)

                elif cmd.action == "save":
                    logging.info(f"SAVING...")
                    # create packet of a dictionary to send back
                    data_string = pickle.dumps(self.pos)
                    # send it through the socket
                    self.sock.send(data_string)
                    logging.info("SENT POS INFO")

                elif cmd.action == "load":
                    # move to pos
                    logging.info(f"MOVING TO :: {cmd.pos}")
                    # height
                    height_diff = cmd.pos["height"] - self.pos["height"]
                    self.plan_rotate(axis="height", distance=height_diff)
                    # width
                    width_diff = cmd.pos["width"] - self.pos["width"]
                    self.plan_rotate(axis="width", distance=width_diff)
                    # pitch
                    pitch_diff = cmd.pos["pitch"] - self.pos["pitch"]
                    self.plan_rotate(axis="pitch", distance=pitch_diff)
                    # yaw
                    yaw_diff = cmd.pos["yaw"] - self.pos["yaw"]
                    self.plan_rotate(axis="yaw", distance=yaw_diff)
                    # roll
                    roll_diff = cmd.pos["roll"] - self.pos["roll"]
                    self.plan_rotate(axis="roll", distance=roll_diff)

                elif cmd.action == "reset":
                    # reset all pos, move back to 0
                    logging.info("RESET POS TO ORIGIN")
                    self.reset()
                    pass  # todo move 

                elif cmd.action == "close":
                    # close the socket nicely, reset to 0
                    self.reset()
                    self.close()

    def close(self):
        """
        Handle closing down of machine
        :return:
        """
        self.reset()
        self.sock.close()
        sys.exit(0)

    def reset(self):
        """
        ATTEMPT to move back to home positions
        """
        height_diff = 0 - self.pos["height"]
        width_diff = 0 - self.pos["width"]
        pitch_diff = 0 - self.pos["pitch"]
        yaw_diff = 0 - self.pos["yaw"]
        roll_diff = 0 - self.pos["roll"]

        self.plan_rotate(axis='height', distance=height_diff)
        self.plan_rotate(axis='width', distance=width_diff)
        self.plan_rotate(axis='pitch', distance=pitch_diff)
        self.plan_rotate(axis='raw', distance=yaw_diff)
        self.plan_rotate(axis='roll', distance=roll_diff)

    def plan_rotate(self, axis: str, distance: int):
        """
        Figure out how much we can rotate:
        Note, we are microstepping here (360/(200*4)) == 0.45 degrees per step.
        We will only move the amount that is permitted by the limits set in self.setup()

        :param axis: raw, roll, pitch
        :param distance: number of steps to move
        """
        logging.info(f"MOVING {axis} -> degrees[{0.45*distance}]:steps[{distance}]")

        buffer_amount: int = 0
        if distance < 0:
            # we are moving a negative amount - get negative limit
            if self.pos[axis] > 0:
                buffer_amount = self.limits[axis][0] - (-1 * self.pos[axis])
            elif self.pos[axis] < 0:
                buffer_amount = self.limits[axis][0] + self.pos[axis]
            else:
                buffer_amount = self.limits[axis][0]
        elif distance > 0:
            # we are moving a positive amount - get positive limit
            if self.pos[axis] > 0:
                buffer_amount = self.limits[axis][1] - self.pos[axis]
            elif self.pos[axis] < 0:
                buffer_amount = self.limits[axis][1] + (-1 * self.pos[axis])
            else:
                buffer_amount = self.limits[axis][1]

        logging.info(f"buffer to move -> {buffer_amount}")

        if distance > buffer_amount:
            logging.info(f"DISTANCE TOO GREAT -> TRY AGAIN")
            return

        # move the motor
        self.perform_movement(axis, distance)

    def plan_translate(self, axis: str, distance: int):
        """
        Figure out how much we can rotate:
        We will only move the amount that is permitted by the limits set in self.setup()
        :param axis: height, width
        :param distance: number of steps to move
        :return:
        """
        # todo sort out here
        # logging.info(f"MOVING {axis} -> degrees[{0.01 * distance}]:steps[{distance}]")  # todo change
        # buffer_amount: int = 0
        # if distance < 0:
        #     # we are moving a negative amount - get negative limit
        #     if self.pos[axis] > 0:
        #         buffer_amount = self.limits[axis][0] - (-1 * self.pos[axis])
        #     elif self.pos[axis] < 0:
        #         buffer_amount = self.limits[axis][0] + self.pos[axis]
        #     else:
        #         buffer_amount = self.limits[axis][0]
        # elif distance > 0:
        #     # we are moving a positive amount - get positive limit
        #     if self.pos[axis] > 0:
        #         buffer_amount = self.limits[axis][1] - self.pos[axis]
        #     elif self.pos[axis] < 0:
        #         buffer_amount = self.limits[axis][1] + (-1 * self.pos[axis])
        #     else:
        #         buffer_amount = self.limits[axis][1]
        #
        # logging.info(f"buffer to move -> {buffer_amount}")
        #
        # if distance > buffer_amount:
        #     logging.info(f"DISTANCE TOO GREAT -> TRY AGAIN")
        #     return

        # move the motor
        self.perform_movement(axis, distance)

    def perform_movement(self, axis: str, distance: int):
        """
        Actually move the stepper motors for the specified distance
        :param axis: height, width, raw, roll, pitch
        :param distance: number of steps to move
        """
        direction: int
        if distance < 0:
            direction = stepper.BACKWARD
        elif distance > 0:
            direction = stepper.FORWARD
        else:
            return

        for _ in range(0, distance):
            if axis == 'pitch':
                self.pitch_yaw.stepper1.onestep(direction=direction, style=stepper.MICROSTEP)
            elif axis == 'yaw':
                self.pitch_yaw.stepper2.onestep(direction=direction, style=stepper.MICROSTEP)
            elif axis == 'roll':
                self.roll.stepper1.onestep(direction=direction, style=stepper.MICROSTEP)
            elif axis == 'height':
                # interleave movement - strength!
                self.height_motors.stepper1.onestep(direction=direction, style=stepper.INTERLEAVE)
                self.height_motors.stepper2.onestep(direction=direction, style=stepper.INTERLEAVE)

            time.sleep(0.01)

        if axis in ['pitch', 'roll', 'yaw']:
            self.pos[axis] += (distance * 0.45)
        else:
            self.pos[axis] += (distance * 0.01)  # todo check this amount

        logging.info(f"MOVED TO: {self.pos[axis]}")

    def setup(self):
        logging.basicConfig(level=logging.INFO,
                            format='[INFO :: %(asctime)s] :: %(message)s')
        logging.info("Hello, skullpos!")
        self.uuid = "CAFE"
        self.pos = dict()  # used to store info on servo positions
        self.pos['height'] = 0
        self.pos['pitch'] = 0
        self.pos['yaw'] = 0
        self.pos['roll'] = 0
        self.pos['width'] = 0

        # define limits for the stepper motors
        self.limits = dict()
        self.limits['height'] = (100, 500)  # todo check
        self.limits['width'] = (100, 500)  # todo check
        self.limits['pitch'] = (45, 45)  # todo check
        self.limits['yaw'] = (45, 45)  # todo check
        self.limits['roll'] = (45, 45)  # todo check

        # initiate the steppers
        self.width_motor = MotorKit(address=0x60)  # todo fix addresses
        self.height_motors = MotorKit(address=0x61)
        self.pitch_yaw = MotorKit(address=0x62, steppers_microsteps=4)
        self.roll = MotorKit(address=0x63, steppers_microsteps=4)

    def bluetooth_setup(self):
        """
        Setup the bluetooth connection (wait until we recv conn)
        """
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
    if sys.argv[1] == "demo":
        rasp = Rasp(True)
    else:
        rasp = Rasp(False)
