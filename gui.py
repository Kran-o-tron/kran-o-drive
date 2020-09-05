import argparse
from socket import socket, AF_INET, SOCK_STREAM
import tkinter as tk
import tkinter.ttk as ttk
import time


class SkullGuiApp:

    def __init__(self, master=None, mach_port=0, iso=False):

        if mach_port != 0:
            # connect to port of main thread!
            self.s = socket(AF_INET, SOCK_STREAM)
            print("Connecting...")
            # for i in range(0, 5):
                # try:
            time.sleep(2)
            try:
                self.s.connect(('', mach_port))
            except Exception as e:
                # print(e)
                exit(1)

            print("Connected!")

        # build ui
        main = ttk.Frame(master)

        # save window
        saveload = ttk.Frame(main)
        saveload_inner = ttk.Frame(saveload)
        playback_inner = ttk.Frame(saveload)
        List_Button = ttk.Button(saveload)
        List_Button.config(text='LIST')
        List_Button.pack(side='top')
        Reset_Button = ttk.Button(saveload)
        Reset_Button.config(text='RESET')
        Reset_Button.pack(side='top')
        Load_Label = ttk.Label(saveload_inner)
        Load_Label.config(anchor='w', cursor='bottom_side', font='application',
                          justify='right')
        Load_Label.config(takefocus=False, text='Load File:')
        Load_Label.pack(side='top')
        self.Load_Entry = ttk.Entry(saveload_inner)
        self.Load_Entry.config(cursor='based_arrow_down')
        self.Load_Entry.pack(side='top')
        Load_Button = ttk.Button(saveload_inner)
        Load_Button.config(text='LOAD')
        Load_Button.pack(side='top')

        Save_Label = ttk.Label(saveload_inner)
        Save_Label.config(text='Save File:')
        Save_Label.pack(side='top')
        self.Save_Entry = ttk.Entry(saveload_inner)
        self.Save_Entry.config(takefocus=True)
        self.Save_Entry.pack(side='top')
        Save_Button = ttk.Button(saveload_inner)
        Save_Button.config(text='SAVE')
        Save_Button.pack(side='top')
        saveload_inner.config(height='200', width='200')
        saveload_inner.pack(anchor='s', side='left')
        saveload.config(height='200', width='200')
        saveload.pack(anchor='w', side='left')

        Playback_Label = ttk.Label(saveload_inner)
        Playback_Label.config(text='Playback File:')
        Playback_Label.pack(side='top')
        self.Playback_Entry = ttk.Entry(saveload_inner)
        self.Playback_Entry.config(takefocus=True)
        self.Playback_Entry.pack(side='top')
        Realtime_Button = ttk.Button(saveload_inner)
        Realtime_Button.config(text='REALTIME PLAYBACK')
        Realtime_Button.pack(side='top')
        staggered_Button = ttk.Button(saveload_inner)
        staggered_Button.config(text='STAGGERED PLAYBACK')
        staggered_Button.pack(side='top')

        final_Button = ttk.Button(saveload_inner)
        final_Button.config(text='FINAL PLAYBACK')
        final_Button.pack(side='top')

        Load_Button.configure(command=self.load)
        Save_Button.configure(command=self.save)
        Realtime_Button.configure(command=self.realtime)
        staggered_Button.configure(command=self.staggered)
        final_Button.configure(command=self.final)
        Reset_Button.configure(command=self.reset)
        List_Button.configure(command=self.list)

        # step amount
        step_label = ttk.Label(main)
        step_label.config(compound='top', cursor='arrow', text='Step Amount')
        step_label.pack(side='top')
        self.step_entry = ttk.Entry(main)
        self.step_entry.config(justify='center')
        _text_ = '''0'''
        self.step_entry.delete('0', 'end')
        self.step_entry.insert('0', _text_)
        self.step_entry.pack(side='top')
        self.step_entry.bind("<Return>", self.update_steps)
        self.step_entry.pack_propagate(0)

        # translate
        transfer_label = ttk.Frame(master)
        self.degrees_label = ttk.Label(transfer_label)
        self.degrees_label.config(text='Degrees: 0')
        self.degrees_label.pack(side='top')
        self.distance_label = ttk.Label(transfer_label)
        self.distance_label.config(text='Translation (mm): 0')
        self.distance_label.pack(side='top')
        transfer_label.config(height='200', width='200')
        transfer_label.pack(side='top')

        # height
        Height_Frame = ttk.Frame(main)
        Height_Label = ttk.Label(Height_Frame)
        Height_Label.config(text='Height')
        Height_Label.pack(anchor='n', side='top')
        Height_Plus = ttk.Button(Height_Frame)
        Height_Plus.config(text='Λ')
        Height_Plus.pack(side='top')
        Height_Minus = ttk.Button(Height_Frame)
        Height_Minus.config(text='V')
        Height_Minus.pack(side='top')
        Height_Value = ttk.Label(Height_Frame)
        Height_Value.config(text='0')
        Height_Value.pack(side='top')
        Height_Frame.config(height='200', width='200')
        Height_Frame.pack(side='left')

        Height_Plus.configure(command=lambda: self.button("Height_Plus"))
        Height_Minus.configure(command=lambda: self.button("Height_Minus"))

        # width
        Width_Frame = ttk.Frame(main)
        Width_Label = ttk.Label(Width_Frame)
        Width_Label.config(text='Width')
        Width_Label.pack(anchor='n', side='top')
        frame_10 = ttk.Frame(Width_Frame)
        Width_Minus = ttk.Button(frame_10)
        Width_Minus.config(text='<')
        Width_Minus.pack(side='left')
        Width_Plus = ttk.Button(frame_10)
        Width_Plus.config(text='>')
        Width_Plus.pack(side='top')
        frame_10.config(height='200', width='200')
        frame_10.pack(side='top')
        Width_Value = ttk.Label(Width_Frame)
        Width_Value.config(text='0')
        Width_Value.pack(side='top')
        Width_Frame.config(height='200', width='200')
        Width_Frame.pack(anchor='e', side='left')

        Width_Plus.configure(command=lambda: self.button("Width_Plus"))
        Width_Minus.configure(command=lambda: self.button("Width_Minus"))

        # pitch
        Pitch_Frame = ttk.Frame(main)
        Pitch_Label = ttk.Label(Pitch_Frame)
        Pitch_Label.config(text='Pitch')
        Pitch_Label.pack(anchor='n', side='top')
        Pitch_Plus = ttk.Button(Pitch_Frame)
        Pitch_Plus.config(text='Λ')
        Pitch_Plus.pack(side='top')
        Pitch_Minus = ttk.Button(Pitch_Frame)
        Pitch_Minus.config(text='V')
        Pitch_Minus.pack(side='top')
        Pitch_Value = ttk.Label(Pitch_Frame)
        Pitch_Value.config(text='0')
        Pitch_Value.pack(side='top')
        Pitch_Frame.config(height='200', width='200')
        Pitch_Frame.pack(side='left')

        Pitch_Plus.configure(command=lambda: self.button("Pitch_Plus"))
        Pitch_Minus.configure(command=lambda: self.button("Pitch_Minus"))

        # yaw
        Yaw_Frame = ttk.Frame(main)
        Yaw_Label = ttk.Label(Yaw_Frame)
        Yaw_Label.config(text='Yaw')
        Yaw_Label.pack(anchor='n', side='top')
        yf = ttk.Frame(Yaw_Frame)
        Yaw_Minus = ttk.Button(yf)
        Yaw_Minus.config(text='<')
        Yaw_Minus.pack(side='left')
        Yaw_Plus = ttk.Button(yf)
        Yaw_Plus.config(text='>')
        Yaw_Plus.pack(side='top')
        yf.config(height='200', width='200')
        yf.pack(side='top')
        Yaw_Value = ttk.Label(Yaw_Frame)
        Yaw_Value.config(text='0')
        Yaw_Value.pack(side='top')
        Yaw_Frame.config(height='200', width='200')
        Yaw_Frame.pack(side='left')

        Yaw_Plus.configure(command=lambda: self.button("Yaw_Plus"))
        Yaw_Minus.configure(command=lambda: self.button("Yaw_Minus"))

        # roll
        Roll_Frame = ttk.Frame(main)
        Roll_Label = ttk.Label(Roll_Frame)
        Roll_Label.config(text='Roll')
        Roll_Label.pack(anchor='n', side='top')
        rf = ttk.Frame(Roll_Frame)
        Roll_Minus = ttk.Button(rf)
        Roll_Minus.config(text='<')
        Roll_Minus.pack(side='left')
        Roll_Plus = ttk.Button(rf)
        Roll_Plus.config(text='>')
        Roll_Plus.pack(side='top')
        rf.config(height='200', width='200')
        rf.pack(side='top')
        Roll_Value = ttk.Label(Roll_Frame)
        Roll_Value.config(text='0')
        Roll_Value.pack(side='top')
        Roll_Frame.config(height='200', width='200')
        Roll_Frame.pack(side='left')

        Roll_Plus.configure(command=lambda: self.button("Roll_Plus"))
        Roll_Minus.configure(command=lambda: self.button("Roll_Minus"))

        # commands
        Commands_Frame = ttk.Frame(main)
        Commands_Label = ttk.Label(Commands_Frame)
        Commands_Label.config(text='Commands Sent:')
        Commands_Label.pack(side='top')
        self.Commands_Window = tk.Text(Commands_Frame, width=15, height=10)
        self.Commands_Window.config(state=tk.DISABLED)
        self.Commands_Window.pack(anchor='s', expand='true', fill='both',
                                  side='bottom')
        Commands_Frame.config(height='200', width='200')
        Commands_Frame.pack(expand='true', fill='both', side='top')

        # main
        main.config(height='200', width='200')
        main.pack(side='top')

        # Main widget
        self.mainwindow = main

        if not iso:
            self.mainwindow.mainloop()

    def update_steps(self, event ):
        try:
            step_size = int(self.step_entry.get())
        except ValueError as e:
            print("GUI: INVALID STEP SIZE - NO COMMAND SENT")
            return  # end step attempt

        self.degrees_label.config(text=f"Degrees: {step_size * 0.45}")
        self.distance_label.config(text=f"Translation (mm): {step_size * 0.1}")

    def print(self, string: str):
        self.Commands_Window.config(state=tk.NORMAL)
        self.Commands_Window.insert(tk.END, string + '\n')
        self.Commands_Window.config(state=tk.DISABLED)
        self.Commands_Window.see(tk.END)

    def button(self, command):
        # get value from entry
        try:
            step_size = int(self.step_entry.get())
        except ValueError as e:
            print("GUI: INVALID STEP SIZE - NO COMMAND SENT")
            return  # end step attempt

        split = command.split("_")
        if split[1] == "Plus":
            # send pos value
            msg = f"{split[0].lower()}::{step_size}"
        else:
            # send neg value
            msg = f"{split[0].lower()}::{-step_size}"

        self.print(msg)

        self.send(msg)

    def list(self):
        self.print("list")
        self.send("list")

    def save(self):
        filename = self.Save_Entry.get()
        self.print(f"save {filename}")
        self.send(f"save::{filename}")

    def load(self):
        filename = self.Load_Entry.get()
        self.print(f"load {filename}")
        self.send(f"load::{filename}")

    def realtime(self):
        filename = self.Playback_Entry.get()
        if filename == "":
            self.print("NO FILE")
            return
        cmd1 = "playback::IRL"
        cmd2 = f"playback::{filename}"
        self.print(cmd1)
        self.print(cmd2)
        self.send(cmd1)
        self.send(cmd2)

    def staggered(self):
        filename = self.Playback_Entry.get()
        if filename == "":
            self.print("NO FILE")
            return
        cmd1 = "playback::CONTROL"
        cmd2 = f"playback::{filename}"
        self.print(cmd1)
        self.print(cmd2)
        self.send(cmd1)
        self.send(cmd2)

    def final(self):
        filename = self.Playback_Entry.get()
        if filename == "":
            self.print("NO FILE")
            return
        cmd2 = f"playback_final::{filename}"
        self.print(cmd2)
        self.send(cmd2)

    def reset(self):
        self.print("reset")
        self.send("reset")

    def send(self, cmd: str):
        self.s.sendall(cmd.encode())

    def run(self):
        self.mainwindow.mainloop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int, help="port for mach.py connection")
    args = parser.parse_args()
    print(args.port)

    root = tk.Tk()
    root.title("SkullPos")
    root.resizable(False, False)
    app = SkullGuiApp(root, args.port, True)
    app.run()
