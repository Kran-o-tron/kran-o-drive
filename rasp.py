import pickle
import sys
import os
import socket
import logging
import time
from decimal import Decimal
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper
from skullpkt import Skullpkt
import tty
import termios

def unix_getchar():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


class Rasp:
    """Class to be run on a raspberry pi server

    Handles the logic for receiving info from host and controlling devices over
    GPIO.
    """

    ANGLE_STEP = Decimal('0.9')
    TRANSLATION_STEP = Decimal('0.02')

    def __init__(self, demo: bool):
        self.uuid = None
        self.pos = None
        self.limits = None
        self.width: MotorKit = None
        self.height_motors: MotorKit = None
        self.roll: MotorKit = None
        self.yaw_pitch_motors: MotorKit = None
        self.roll_pan_motors: MotorKit = None
        self.sock = None
        self.client_info = None
        self.server_sock = None
        self.broken_steppers = False  # flips to true if we cannot find steppers.

        self.setup()  # start variables and wait for connection
        self.demo = True
        self.standardise()

        if not demo:
            self.demo = False
            self.network_setup()
            self.mainloop()  # enter connection loop

    def standardise(self):
        input("HIT ENTER TO BEGIN STANDARDISATION")
        GO = True
        while GO:
            for axis in ['height', 'width', 'pitch', 'yaw', 'roll']:
                print("MOVING", axis)
                while True:
                    char = unix_getchar()
                    if char == 'w':
                        if axis in ['height', 'width']:
                            # reversed directions
                            direction = stepper.BACKWARD
                        else:
                            direction = stepper.FORWARD
                    elif char == 's':
                        if axis in ['height', 'width']:
                            # reversed directions
                            direction = stepper.FORWARD
                        else:
                            direction = stepper.BACKWARD
                    elif char == '/':
                        print('next axis...')
                        break
                    elif char == '=':
                        print("DONE... EXITING")
                        GO = False
                        return
                    else:
                        print("BAD KEY, CONTINUING...")
                        continue

                    if axis == 'pitch':
                        self.yaw_pitch_motors.stepper2.onestep(direction=direction,
                                                               style=stepper.INTERLEAVE)
                    elif axis == 'yaw':
                        self.yaw_pitch_motors.stepper1.onestep(direction=direction,
                                                               style=stepper.INTERLEAVE)
                    elif axis == 'roll':
                        self.roll_pan_motors.stepper1.onestep(direction=direction, style=stepper.INTERLEAVE)
                    elif axis == 'width':
                        for _ in range(10):
                            self.roll_pan_motors.stepper2.onestep(direction=direction, style=stepper.INTERLEAVE)
                    elif axis == 'height':
                        for _ in range(10):
                            self.height_motors.stepper2.onestep(direction=direction, style=stepper.INTERLEAVE)
                            self.height_motors.stepper1.onestep(direction=direction, style=stepper.INTERLEAVE)

                    time.sleep(0.01)

    def mainloop(self):
        """Main execution loop for Mach. Waits for commands and executes their
        corresponding logic.
        """
        while True:
            try:
                data = self.sock.recv(4096)
            except Exception as e:
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
                    logging.info("ATTEMPT MOVE :: %s :: %d" % (cmd.action, cmd.amount))
                    self.plan_movement(cmd.action, cmd.amount)
                elif cmd.action in ['height', 'width']:
                    self.plan_movement(cmd.action, cmd.amount)

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
                    self.plan_movement(axis="height", distance=height_diff)
                    # width
                    width_diff = cmd.pos["width"] - self.pos["width"]
                    self.plan_movement(axis="width", distance=width_diff)
                    # pitch
                    pitch_diff = cmd.pos["pitch"] - self.pos["pitch"]
                    self.plan_movement(axis="pitch", distance=pitch_diff)
                    # yaw
                    yaw_diff = cmd.pos["yaw"] - self.pos["yaw"]
                    self.plan_movement(axis="yaw", distance=yaw_diff)
                    # roll
                    roll_diff = cmd.pos["roll"] - self.pos["roll"]
                    self.plan_movement(axis="roll", distance=roll_diff)

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
        height_diff = Decimal('0') - self.pos["height"]
        width_diff = Decimal('0') - self.pos["width"]
        pitch_diff = Decimal('0') - self.pos["pitch"]
        yaw_diff = Decimal('0') - self.pos["yaw"]
        roll_diff = Decimal('0') - self.pos["roll"]

        self.plan_movement(axis='height', distance=height_diff)
        self.plan_movement(axis='width', distance=width_diff)
        self.plan_movement(axis='pitch', distance=pitch_diff)
        self.plan_movement(axis='raw', distance=yaw_diff)
        self.plan_movement(axis='roll', distance=roll_diff)

    def plan_movement(self, axis: str, distance: int):
        """
        Figure out how much we can rotate:
        Note, we are microstepping here (360/(200*4)) == 0.45 degrees per step.
        We will only move the amount that is permitted by the limits set in self.setup()

        :param axis: raw, roll, pitch
        :param distance: number of steps to move
        """
        buffer_amount: int = 0
        if distance < 0:
            # we are moving a negative amount - get negative limit
            if self.pos[axis] > 0:
                buffer_amount = self.limits[axis][0] - (Decimal('-1') * self.pos[axis])
            elif self.pos[axis] < 0:
                buffer_amount = self.limits[axis][0] + self.pos[axis]
            else:
                buffer_amount = self.limits[axis][0]
        elif distance > 0:
            # we are moving a positive amount - get positive limit
            if self.pos[axis] > 0:
                buffer_amount = self.limits[axis][1] - self.pos[axis]
            elif self.pos[axis] < 0:
                buffer_amount = self.limits[axis][1] + (Decimal('-1') * self.pos[axis])
            else:
                buffer_amount = self.limits[axis][1]

        if axis in ['pitch', 'roll', 'yaw']:
            logging.info(f"MOVING {axis} -> degrees[{Rasp.ANGLE_STEP * distance}]:steps[{distance}]")
            logging.info(f"buffer to move -> {buffer_amount}")

            if distance * Rasp.ANGLE_STEP > buffer_amount:
                logging.info(f"DISTANCE TOO GREAT -> TRY AGAIN")
                return
        else:
            logging.info(f"MOVING {axis} -> m[{distance/Rasp.TRANSLATION_STEP}]:steps[{distance}]")
            logging.info(f"buffer to move -> {buffer_amount}")

            if distance * Rasp.TRANSLATION_STEP > buffer_amount:
                logging.info(f"DISTANCE TOO GREAT -> TRY AGAIN")
                return

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
            if axis in ['height', 'width']:
                # reversed directions
                direction = stepper.FORWARD
            else:
                direction = stepper.BACKWARD
        elif distance > 0:
            if axis in ['height', 'width']:
                # reversed directions
                direction = stepper.BACKWARD
            else:
                direction = stepper.FORWARD
        else:
            return

        # self.height_motors.stepper1.release()
        # self.height_motors.stepper2.release()

        if not self.broken_steppers:
            # print(axis, distance, direction)
            for _ in range(0, abs(distance)):
                if axis == 'pitch':
                    self.yaw_pitch_motors.stepper2.onestep(direction=direction, style=stepper.MICROSTEP)
                    time.sleep(0.01)
                elif axis == 'yaw':
                    self.yaw_pitch_motors.stepper1.onestep(direction=direction,
                                                           style=stepper.MICROSTEP)
                    time.sleep(0.01)
                elif axis == 'roll':
                    self.roll_pan_motors.stepper1.onestep(direction=direction, style=stepper.MICROSTEP)
                    time.sleep(0.01)
                elif axis == 'width':
                    self.roll_pan_motors.stepper2.onestep(direction=direction,
                                                          style=stepper.MICROSTEP)
                elif axis == 'height':
                    # interleave movement - strength!
                    # reverse the movement (wiring is backwards sadly)
                    # print(axis, distance, direction)
                    self.height_motors.stepper2.onestep(direction=direction, style=stepper.SINGLE)
                    self.height_motors.stepper1.onestep(direction=direction, style=stepper.SINGLE)

                # time.sleep(0.01)
        else:
            print("Steppers cannot be accessed! Restart & check the wiring!")

        # self.height_motors.stepper1.release()
        # self.height_motors.stepper2.release()

        if axis in ['pitch', 'roll', 'yaw']:
            self.pos[axis] += (distance * Rasp.ANGLE_STEP)
        else:
            self.pos[axis] += (distance * Rasp.TRANSLATION_STEP)  # todo check this amount

        logging.info(f"MOVED TO: {self.pos[axis]}")
        if self.gui_status:
            # print("sending...")
            self.gui_conn.send(f"{axis}::{str(self.pos[axis])}".encode())

    def setup(self):
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] :: %(message)s')
        logging.info("Hello, Kran-o-tron!")
        self.uuid = "CAFE"
        self.pos = dict()  # used to store info on servo positions
        self.pos['height'] = Decimal('0.0')
        self.pos['pitch'] = Decimal('0.0')
        self.pos['yaw'] = Decimal('0.0')
        self.pos['roll'] = Decimal('0.0')
        self.pos['width'] = Decimal('0.0')

        # define limits for the stepper motors
        self.limits = dict()
        self.limits['height'] = (Decimal('10000'), Decimal('10000'))  # todo check
        self.limits['width'] = (Decimal('10000'), Decimal('10000'))  # todo check
        self.limits['pitch'] = (Decimal('30'), Decimal('30'))  # todo check
        self.limits['yaw'] = (Decimal('30'), Decimal('30'))  # todo check
        self.limits['roll'] = (Decimal('30'), Decimal('30'))  # todo check

        # initiate the steppers
        try:
            print("Init motors...")
            self.yaw_pitch_motors = MotorKit(address=0x60, steppers_microsteps=4)
            self.roll_pan_motors = MotorKit(address=0x61, steppers_microsteps=4)
            self.height_motors = MotorKit(address=0x62)

            self.yaw_pitch_motors.stepper1.release()
            self.yaw_pitch_motors.stepper2.release()
            self.roll_pan_motors.stepper1.release()
            self.roll_pan_motors.stepper2.release()
            self.height_motors.stepper1.release()
            self.height_motors.stepper2.release()

        except Exception as e:
            print(e)
            print("Couldn't find the stepper hats! Check the wiring!")
            self.broken_steppers = True

    def network_setup(self):
        """
        Setup the ethernet connection (wait until we recv conn)
        """
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind(("", 44444))
        self.server_sock.listen(1)

        self.gui_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gui_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.gui_sock.bind(("", 23456))

        cmd = 'ifconfig eth0 | grep "inet " | cut -d " " -f10'
        logging.info(f"LISTENING on TCP/IP, record the following address...")
        ip = os.system(cmd)
        # wait for a connection!
        self.sock, self.client_info = self.server_sock.accept()
        logging.info("ACCEPTED :: %s" % self.client_info[0])

        # print("hi")
        try:
            # print("waiting for GUI")
            self.gui_sock.settimeout(5)
            self.gui_sock.listen(1)
            self.gui_conn, self.gui_info = self.gui_sock.accept()
            logging.info("CONNECTED TO GUI")
            self.gui_status = True
        except socket.timeout:
            print("No GUI instance found...")
            self.gui_status = False


if __name__ == "__main__":
    if sys.argv[1] == "demo":
        rasp = Rasp(True)
    else:
        rasp = Rasp(False)
