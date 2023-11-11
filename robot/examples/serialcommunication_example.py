import serial
import time
from serial.serialutil import SerialException

# check this: https://pyserial.readthedocs.io/en/latest/shortintro.html
# check this too: https://pyserial.readthedocs.io/en/latest/pyserial_api.html

# TODO: Add correct PORT
# 1kOhm Pullup on Rx
"""2 Bytes Command|Parameter \n m 5 \n -> Move 5 cm """

PORT = "/dev/ttyTHS1"
BAUDRATE = 38400

WRITE_TIMEOUT = 2
READ_TIMEOUT = 2

try:
    ser = serial.Serial(
        PORT,
        BAUDRATE,
        write_timeout=WRITE_TIMEOUT,
        timeout=READ_TIMEOUT,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
    )
    print(ser.name)
    while True:
        time.sleep(0.01)
        # Jetson Bootup Command
        ser.write("Ping\n".encode())
        # ser.write(bytearray.fromhex(11))
        print(ser.read())

except SerialException as exp:
    print("SerialException")
    print(exp)

except Exception as exp:
    print("OtherException")
    print(exp)
