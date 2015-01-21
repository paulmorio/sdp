import Tkinter as tk
from serial import Serial

class Robot(Serial):
    """Serial connection setup, IO, and robot actions."""

    def __init__(self, port="/dev/ttyACM0", rate=115200, timeout=1):
        """
        Create a robot object which provides action methods and opens a serial
        connection.

        :param port: Default is "/dev/ttyACM0". This changes based on
        platform, etc. The default should correspond to what shows on the DICE
        machines.

        :param rate: Baud rate
        :param timeout: Write timeout in seconds
        :return:
        """
        super(Robot, self).__init__(port, rate, timeout=timeout)

    def read_all(self):
        """
        Read all data on serial.

        :return: Byte representation of data on serial.
        """
        return self.read(self.inWaiting())