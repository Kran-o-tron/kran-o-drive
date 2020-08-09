import argparse
import bluetooth
import json
import pickle
import signal
import sys
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

from cmd import CMD
from skullpkt import Skullpkt


def signal_handler(sig, frame):
    """capture ^c for polite exiting"""
    print(' -> Shutting down...')
    sys.exit(0)


class Mach:
    """Class instantiated on the 'host' laptop, i.e. the device that issues
     commands to SkullBot

    Issues commands to the RPI to control it, either through a GUI or CLI
    interface.
    """

    def __init__(self, bluetooth_addr: str, gui=False):
        self.bluetooth_addr = bluetooth_addr
        self.bluetooth_socket = None  # socket over which we comm with pi.
        self.save_wait = False  # indicate we need to recv from the sock
        self.profiles = None  # saved profiles
        self.profile_name = None  # current file to save to
        self.gui_socket = None  # socket to comm with GUI over.
        self.gui_conn = None  # connection between gui and machine

        if gui:
            self.setup_gui()

        self.load_from_disk()
        self.connect()
        self.mainloop(gui)

    def setup_gui(self):
        self.gui_socket = socket(AF_INET, SOCK_STREAM)
        self.gui_socket.bind(('', 0))
        self.gui_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        # wait for connection
        print(
            "Started in GUI mode, execute the following command to interface "
            "with skullpos")
        print(f"\t > python3 gui.py {self.gui_socket.getsockname()[1]}")
        self.gui_socket.listen()
        print("waiting...")
        self.gui_conn, addr = self.gui_socket.accept()

    def mainloop(self, gui):
        """Main execution loop for Mach. Waits for commands and executes their
        corresponding logic.

        :param gui: boolean: false - use cli, true - use gui
        """
        self.welcome(gui)  # print nice welcome to the terminal

        while True:
            close = False
            pkt = Skullpkt()

            # -------- INPUT --------
            if not gui:
                # cli input
                data = input("> ")
            else:
                # gui socket input
                data = self.gui_conn.recv(1024)
                data = data.decode()
                print(f"$ {data}")

            if not data:
                break  # end if data is unintelligible.

            command_list = data.split(" ")
            for command in command_list:
                # -------- reset & close --------
                if command in ['reset', 'close']:
                    c = CMD(command)
                    pkt.add_cmd(c)
                    if command == 'close':
                        close = True

                # -------- save --------
                elif command.startswith("save::"):
                    args = command.split("::")
                    c = CMD('save')
                    pkt.add_cmd(c)
                    self.do_save(args)

                # -------- load --------
                elif command.startswith("load::"):
                    args = command.split("::")
                    cmd = CMD('load')
                    self.do_load(args, cmd, pkt)

                # -------- list --------
                elif command == "list":
                    for entry in self.profiles.keys():
                        print(f'{entry} -> {self.profiles[entry]}')

                # -------- help --------
                elif command == "?":
                    print("Valid commands...")
                    print(CMD.permitted_cmds())

                # -------- move --------
                elif command.startswith(('pitch', 'yaw', 'height', 'roll',
                                         'width')):
                    args = command.split("::")
                    self.do_move(args, command, pkt)

                # -------- BAD CMD --------
                else:
                    print(f"\t<{command}> BAD COMMAND (DOESN'T EXIST)")

            # -------- SEND OVER SOCK --------
            if len(pkt.get_pkt_cmds()) != 0:
                data_string = pickle.dumps(pkt)
                self.bluetooth_socket.send(
                    data_string)  # send along the socket to the rpi

            # -------- SAVE RESPONSE --------
            if self.save_wait:
                # wait for save data from RPI
                self.save_wait = False
                data = self.bluetooth_socket.recv(4096)
                data = pickle.loads(data)
                print(data)
                self.profiles[self.profile_name] = data
                self.save_to_disk()

            # -------- END CONN --------
            if close:
                self.bluetooth_socket.close()
                sys.exit(0)

    def do_move(self, args, command, pkt):
        """Logic for controlling move commands to the pi.

        :param args: list of command attributes
        :param command: full command
        :param pkt: packet to issue command to
        """
        try:
            c = CMD(args[0], int(args[1]))
            pkt.add_cmd(c)
        except ValueError as e:
            print(f"\t<{command}> BAD COMMAND (ERROR)")

    def do_load(self, args, cmd, pkt):
        """Logic to load position profile to the pi.

        :param args: list of command attributes
        :param cmd: command object to load position attr into to send to pi
        :param pkt: packet object to hold commands.
        """
        self.profile_name = args[1]
        if self.profile_name in self.profiles.keys():
            print("LOADING PROFILE...")
            cmd.pos = self.profiles[self.profile_name]
            pkt.add_cmd(cmd)
        else:
            print("ERROR: PROFILE DOES NOT EXIST")

    def do_save(self, args):
        """Logic to handle saving of position data from the pi.

        :param args: list of command attributes
        """
        self.save_wait = True
        # -------- PROFILE PRESENT? --------
        self.profile_name = args[1]  # save profile name
        if self.profile_name in self.profiles.keys():
            print("=========================")
            string = input(
                f'Profile present with values {self.profiles[args[1]]}\n'
                f'Do you want to overwrite? [Y/n] ')
            print("=========================")
            if string == "Y":
                # -------- OVERWRITE --------
                print("OVERWRITING")
                self.profiles[args[1]] = dict()
            else:
                # -------- CANCEL --------
                print("OVERWRITE CANCELLED")
                self.save_wait = False

    def save_to_disk(self):
        # save the profile from the pi to JSON disk.
        with open('profiles.json', 'w') as fp:
            json.dump(self.profiles, fp)

    def load_from_disk(self):
        # load profile from JSON on disk.
        with open('profiles.json') as fp:
            self.profiles = json.loads(fp.read())

    def connect(self):
        """Initiate a connection between host and the pi over bluetooth

        Note: Use of RFCOMM ensures 'reliable' (best effort) delivery!
        """
        # instantiate and connect to bluetooth socket
        service_matches = bluetooth.find_service(address=self.bluetooth_addr)
        first_match = service_matches[0]
        port = first_match["port"]
        name = first_match["name"]
        host = first_match["host"].decode()

        self.bluetooth_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.bluetooth_socket.connect((host, port))

    def welcome(self, gui):
        """Welcome msg to terminal

        :param gui: whether GUI or CLI mode - each has a diff msg.
        """
        print("==========================================================")
        if gui:
            print("Connected. Use the GUI window to send commands")
        else:
            print("Connected. Give a command in the format -> <cmd>::<amount>")
            print("Type ? or help for a list of commands.")
        print("==========================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='skullpos client')
    parser.add_argument('bluetooth_addr', type=str)
    parser.add_argument('-gui', action='store_true')
    signal.signal(signal.SIGINT, signal_handler)
    args = parser.parse_args()
    Mach(args.bluetooth_addr, args.gui)
