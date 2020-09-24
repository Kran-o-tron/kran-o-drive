import time
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper

"""
stepper.SINGLE (default) for a full step rotation to a position where one single coil is powered
stepper.DOUBLE for a full step rotation to position where two coils are powered providing more torque
stepper.INTERLEAVE for a half step rotation interleaving single and double coil positions and torque
stepper.MICROSTEP for a microstep rotation to a position where two coils are partially active
"""

kit1 = MotorKit(address=0x60, steppers_microsteps=8)
kit2 = MotorKit(address=0x61, steppers_microsteps=8)
kit3 = MotorKit(address=0x62)
kit1.stepper1.release()
kit1.stepper2.release()
kit2.stepper1.release()
kit2.stepper2.release()
kit3.stepper1.release()
kit3.stepper2.release()

input()
for i in range(1000):
    for i in range(500):
        print(kit3.stepper2.onestep(direction=stepper.BACKWARD))  # step
        print(kit3.stepper1.onestep(direction=stepper.BACKWARD))  # step
    # print(kit1.stepper2.onestep(direction=stepper.FORWARD, style=stepper.MICROSTEP))  # step
    # print(kit1.stepper2.onestep(direction=stepper.FORWARD, style=stepper.INTERLEAVE))

    # for i in range(280):
    #     print(kit2.stepper2.onestep(direction=stepper.BACKWARD, style=stepper.INTERLEAVE))
    # print(kit3.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.MICROSTEP))  # step
    # functions
    # return the
    # position
    # kit1.stepper2.onestep(direction=stepper.BACKWARD)
    # print(kit.ste)  # step functions return the position
    # time.sleep(0.01)
    # input()

# kit.stepper1.release()
# for i in range(10):
#     step backwards at double
    # print(kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE))
    # time.sleep(0.01)
#
# for i in range(10):
#     print(kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.INTERLEAVE))
#     time.sleep(0.01)
#
# for i in range(10):
#     print(kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.MICROSTEP))
#     time.sleep(0.01)
