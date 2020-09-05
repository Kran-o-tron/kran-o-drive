import argparse
import os
import json
import pickle
import signal
import sys
import time
from fpdf import FPDF

import socket
from cmd import CMD
from skullpkt import Skullpkt
from typing import Optional
from io import TextIOWrapper
import datetime


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

    def __init__(self, ethernet_address: str, gui=False, playback=True):
        self.ethernet_addr = ethernet_address
        self.playback_enabled = playback
        self.ethernet_socket = None  # socket over which we comm with pi.
        self.save_wait = False  # indicate we need to recv from the sock
        self.profiles = None  # saved profiles
        self.profile_name = None  # current file to save to
        self.gui_socket = None  # socket to comm with GUI over.
        self.gui_conn = None  # connection between gui and machine
        self.f_out: Optional[TextIOWrapper] = None  # file to be written to in playback mode
        self.realtime_playback = False  # either repeat IRL timings, or wait until input confirm
        self.demo = False
        self.last_playback = ""

        if self.playback_enabled:
            self.playback_setup()

        self.load_from_disk()

        if ethernet_address != '0':  # demo purposes
            try:
                self.connect()
            except Exception as e:
                print(e)
                print("couldn't connect! Check if you are connected via ethernet and that you "
                      "have the correct ipv4 address!")
                exit(1)
        else:
            self.demo = True

        if gui:
            self.setup_gui()

        self.mainloop(gui)

    def setup_gui(self):
        self.gui_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gui_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.gui_socket.bind(('', 55555))

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

                # -------- playback --------
                elif command.startswith("playback::"):
                    args = command.split("::")
                    if args[1] == "IRL":
                        self.realtime_playback = True
                    elif args[1] == "CONTROL":
                        self.realtime_playback = False
                    elif args[1] == "START":
                        if not self.playback_enabled:
                            self.playback_enabled = True
                            self.playback_setup()
                        else:
                            print("ERROR! ALREADY RECORDING!")
                    elif args[1] == "END":
                        if not self.playback_enabled:
                            print("ERROR! NOT RECORDING, START WITH `playback::START`")
                        else:
                            self.playback_enabled = False
                            self.f_out.close()
                            self.f_out = None
                            with open(self.last_playback, 'r') as file:
                                pdf = FPDF()
                                pdf.add_page()
                                pdf.set_font("Helvetica", size=12)
                                lines = file.readlines()
                                for i in range(1, len(lines) + 1):
                                    txt = lines[i-1]
                                    pdf.cell(0, 5, txt=txt, ln=i)

                                pdf.output(self.last_playback[:-4] + ".pdf")
                            print("Saved to: " + self.last_playback[:-4] + ".pdf")


                    else:
                        # check if file exists
                        if os.path.exists(f"playbacks/{args[1]}"):
                            self.load_from_playback(f"playbacks/{args[1]}")
                        else:
                            print("BAD PLAYBACK MODE, EITHER `IRL` or `CONTROL` or `FILE_NAME`")

                # -------- playback final --------
                elif command.startswith("playback_final::"):
                    args = command.split("::")
                    self.play_final_pos(f"playbacks/{args[1]}")

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
                self.send_to_pi(pkt)

            # -------- SAVE RESPONSE --------
            if self.save_wait:
                # wait for save data from RPI
                self.save_wait = False
                if not self.demo:
                    data = self.ethernet_socket.recv(4096)
                    data = pickle.loads(data)
                    print(data)
                    self.profiles[self.profile_name] = data
                    self.save_to_disk()

            # -------- END CONN --------
            if close:
                if not self.demo:
                    self.ethernet_socket.close()
                sys.exit(0)

    def send_to_pi(self, pkt):
        data_string = pickle.dumps(pkt)
        if not self.demo:
            self.ethernet_socket.send(data_string)  # send along the socket to the rpi
        # ~~ playback save ~~
        if self.playback_enabled:
            self.save_cmd_for_playback(pkt.get_pkt_cmds())

    def playback_setup(self):
        """
        Logic for handling playback setup
        """
        right_now = datetime.datetime.now()
        file_format = right_now.strftime("%b-%d-%Y(%H.%M.%S)")
        if not os.path.exists('playbacks'):
            os.makedirs('playbacks')
        file_format = f"playbacks/SkullBot_{file_format}.csv"
        print(f"\n:: Saving playback info to {file_format}")
        self.f_out = open(file_format, 'w')
        self.last_playback = file_format

    def save_cmd_for_playback(self, cmd_list: list):
        for cmd in cmd_list:
            print(cmd)
            if cmd.action.startswith('save'):
                continue
            else:
                right_now = datetime.datetime.now()
                date_time = right_now.strftime("%b-%d-%Y(%H:%M:%S)")
                self.f_out.write(f"{date_time},{cmd}\n")  # save the cmd to file

    def load_from_playback(self, file_name: str):
        commands = []
        with open(file_name, 'r') as fp:
            for line in fp.readlines():
                try:
                    time_sent = line.split(',')[0]
                    cmd = line.split(',')[1]
                    commands.append((time_sent, cmd))
                except IndexError as e:
                    print("ERROR: BAD FILE FORMAT")
                    return

        ftr = [3600, 60, 1]  # how many seconds are in each timeslot
        time_str = file_name.split("(")[1].split(")")[0]
        prev_seconds = sum([a * b for a, b in zip(ftr, map(int, time_str.split('.')))])

        for command in commands:
            pkt = Skullpkt()
            cmd = CMD(comm=command[1].split("::")[0], amount=int(command[1].split("::")[1]))
            pkt.add_cmd(cmd)

            if self.realtime_playback:
                time_section = command[0].split("(")[1].split(")")[0]
                current_seconds = sum([a * b for a, b in zip(ftr, map(int, time_section.split(
                    ':')))])
                time_to_wait = current_seconds - prev_seconds
                print(f"Waiting {time_to_wait} seconds...")
                time.sleep(time_to_wait)
            else:
                # wait for user input to move on
                _ = input("Press any button to send next command...")

            # ------- now send to the pi -------
            if len(pkt.get_pkt_cmds()) != 0:
                print(f"Sending... {command[1]}")
                self.send_to_pi(pkt)

    def play_final_pos(self, file_name):
        position = {'height': 0, 'width': 0, 'pitch': 0, 'roll': 0, 'yaw': 0}

        with open(file_name, 'r') as fp:
            for line in fp.readlines():
                try:
                    cmd = line.split(',')[1]
                    position[cmd.split("::")[0]] += int(cmd.split("::")[1])
                except IndexError as e:
                    print("ERROR: BAD FILE FORMAT")
                    return

        print(f"Final position: {position}")

        pkt = Skullpkt()
        cmd = CMD('load')
        cmd.pos = position
        pkt.add_cmd(cmd)

        # ------- now send to the pi -------
        if len(pkt.get_pkt_cmds()) != 0:
            self.send_to_pi(pkt)

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
        """Initiate a connection between host and the pi over ethernet

        Note: Use of TCP (AF_INET) ensures 'reliable' (best effort) delivery!
        """

        self.ethernet_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ethernet_socket.connect((self.ethernet_addr, 44444))  # always connect on port 1

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
    parser.add_argument('ipv4_addr', type=str)
    parser.add_argument('-gui', action='store_true')
    parser.add_argument('-no_playback', action='store_false')
    signal.signal(signal.SIGINT, signal_handler)
    args = parser.parse_args()
    Mach(args.ipv4_addr, args.gui, args.no_playback)


# todo remove self.demo lines
