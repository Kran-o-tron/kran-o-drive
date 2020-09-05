import time
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper

"""
stepper.SINGLE (default) for a full step rotation to a position where one single coil is powered
stepper.DOUBLE for a full step rotation to position where two coils are powered providing more torque
stepper.INTERLEAVE for a half step rotation interleaving single and double coil positions and torque
stepper.MICROSTEP for a microstep rotation to a position where two coils are partially active
"""

kit = MotorKit()

for i in range(10):
    print(kit.stepper1.onestep())  # step functions return the position
    print(kit.ste)  # step functions return the position
    time.sleep(0.01)

for i in range(10):
    # step backwards at double
    print(kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE))
    time.sleep(0.01)

for i in range(10):
    print(kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.INTERLEAVE))
    time.sleep(0.01)

for i in range(10):
    print(kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.MICROSTEP))
    time.sleep(0.01)
