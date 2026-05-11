"""
Simple control interface for using an external UART device to drive a Stepper motor via a TMC2209, or any other
stepper driver with similar dir/step electrical interface.

Pins used:
GPIO:
    - 6: Direction Pin
    - 7: Step Pin
UART1:
    - 4: TX
    - 5: Rx

UART commands are expected to be of the following structure:
bytes: <header><header><direction><angle_lower><angle_higher>
where header is 0x55, direction is 1 or 2, and the angle is given in centi-degrees

e.g. Rotate by 10 degrees clockwise:
 0x555501E803

A limited set of debug information is printed over the USB port if connected.
"""
import time

from machine import Pin, UART

# Constants:
MICRO_STEPS = 64.0  # Microsteps configured on the stepper driver
DEG_PER_STEP = 1.8  # Number of degrees traveled by the motor for a given full step
DEG_PER_MICRO_STEP = DEG_PER_STEP / MICRO_STEPS  # Number of degrees traveled by the motor for a commanded step
HEADER = 0x55  # Header expected in the first two bytes of the UART stream

# Initialize UART1 interface to 9600 parity None
uart1 = UART(1,baudrate=9600, bits=8, parity=None, stop=1, tx=Pin(4), rx=Pin(5))

# Initialize GPIO pins
direction_pin = Pin(6, Pin.OUT)  # Sets the drive direction by pulling the direction pin on TMC2209 high or low
step_pin = Pin(7, Pin.OUT)  # Steps the TMC2209


def write_stepper_command(direc, dtheta):
    """
    Pulls the direction pin either low or high depending on commanded direction and steps the step pin the required
    number of times to rotated by dtheta.

    Limitation: Velocity is currently hard coded based on the wait times between rise and falling edges of the step pin.

    :param int direc: Requested direction of travel. 1 == clockwise, 2 == counterclockwise
    :param float dtheta: Requested angle to rotate by.
    """
    num_steps = int(dtheta / DEG_PER_MICRO_STEP)
    if direc == 1:
        direction_pin.value(1)
    else:
        direction_pin.value(0)

    for i in range(num_steps):
        step_pin.value(1)
        time.sleep_us(20)
        step_pin.value(0)
        time.sleep_us(20)


class BufferState(object):
    """
    State machine states for the UART stream.
    """
    HEADER1 = 0
    HEADER2 = 1
    DIRECTION = 2
    ANGLE1 = 3
    ANGLE2 = 4


parse_state = 0

while True:
    direction = None
    angle = None

    bytes = uart1.read()
    if bytes:
        for byte in bytes:
            if parse_state == BufferState.HEADER1 and byte == HEADER:
                parse_state = BufferState.HEADER2
                print('Header 1 Detected')
                continue
            if parse_state == BufferState.HEADER2 and byte == HEADER:
                parse_state = BufferState.DIRECTION
                print('Header 2 Detected')
                continue

            if parse_state == BufferState.DIRECTION:
                print(byte)
                direction = int(byte)
                if direction not in [1,2]:
                    parse_state = BufferState.HEADER1
                else:
                    parse_state = BufferState.ANGLE1
                    print('Direction Detected')
                    print('Direction: %s' % direction)
            elif parse_state == BufferState.ANGLE1:
                angle = int(byte)
                parse_state = BufferState.ANGLE2
                print('Angle Part 1 Detected')
                print('Angle: %s' % angle)
            elif parse_state == BufferState.ANGLE2:
                angle += int(byte) << 8
                angle /= 100 # Angle input is in centi-degrees
                parse_state = BufferState.HEADER1
                print('Angle Part 2 Detected')
                print('Angle: %s' % angle)
                write_stepper_command(direction, angle)

