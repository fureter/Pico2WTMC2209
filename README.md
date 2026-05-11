Barebones control program for the Pico2W written in Micropython. 

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
