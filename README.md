# SkullPos - software for SkullBot

Craniofacial positioning device w/ bluetooth between a RPI3 and UNIX machine. Interface via command line or graphical interface modes.

![demo](./support/demo.gif)

## Quick Start

Uses Python 3 and the Bluetooth Stack to communicate with a Raspberry Pi.

Run `./rasp-install.sh` to enable all requirements on the Raspberry Pi machine. Similarly `./mach-install.sh` for the client.

Run `./rasp-start.sh` on the Raspberry Pi to begin the server process. Note the bluetooth address in the format ```00:00:00:00:00:00```.

Run `python3 mach.py <addr>` to communicate with the Raspberry Pi, where `<addr>` is the bluetooth address given above. This will connect to the Pi over bluetooth in *command line mode*, thus you will have to issue commands (specified in [Commands](##Commands)).

If using *command line mode* is undesirable, run `python3 mach.py -gui <addr>` in order to initiate *GUI* mode. You can begin a GUI instance on your machine by running `python3 gui.py <port>` where `port` is the number supplied by the `mach.py` instance. This GUI negates the use of the command line interface for easier use, and can be seen below:

![gui](./support/gui.png)

## Commands

Use `pitch`, `yaw`, `roll`, `height` and `width` like so `<cmd>::<amount>` where `amount` is the value to operate the servo by.

`save::<name>` to save the current position of the device to disk for later use.

`load::<name>` to load a profile onto the Pi with the given name from disk.

`list` to see all current profiles on disk.

`reset` to reset all positions to their origin.

`close` to politely close the connection. `^C` also works too.

## Profile format

All position profiles are stored in `profiles.json` in the home directory for easy to edit formatting. See the file for formatting examples.

## Contributors

`m-ish` - Hamish Bultitude
