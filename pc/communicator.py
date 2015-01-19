import io
from serial import *
from select import select


class Communicator:
    """
    Initialise serial connection to robot. Handles communication back and forth.
    """

    def __init__(self, port="/dev/ttyUSB0", rate=115200, timeout=2000, ):
        """
        Create a communicator which acts as an interface for serial
        communication.

        :param port: Default is "/dev/ttyUSB0". This changes based on
        platform, etc. The default should correspond to what shows on the DICE
        machines.
        :param rate: Baud rate
        :param timeout: write timeout in ms
        :return:
        """

        self.serial = None
        self.port = port
        self.rate = rate
        self.timeout = timeout
        self.setup

    def setup(self):
        """ Initialise the serial port. Print an error if already open or if
            failed. """
        if self.serial is None:
            try:
                self.serial = Serial(self.port, self.rate, timeout=self.timeout)
            except SerialException:
                print "Unable to open serial connection. It is likely that " \
                      "the port is incorrect or the device is missing."
        else:
            print "A serial port is already open - go away!"

    def write(self, str):
        """
        Write a string to the serial device.
        :param str: output string
        :return:
        """
        self.serial.write(str)