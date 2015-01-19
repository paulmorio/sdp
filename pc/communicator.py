from serial import *


class Communicator:
    """
    Initialise serial connection to robot. Handles communication back and forth.
    """

    def __init__(self, port="/dev/ttyACM0", rate=115200, timeout=1):
        """
        Create a communicator which acts as an interface for serial
        communication.

        :param port: Default is "/dev/ttyUSB0". This changes based on
        platform, etc. The default should correspond to what shows on the DICE
        machines.

        :param rate: Baud rate
        :param timeout: write timeout in seconds
        :return:
        """

        self.serial = None
        self.port = port
        self.rate = rate
        self.timeout = timeout
        self.setup()

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
        TODO writing ints - need to encode int to C byte representation

        :param str: output string
        :return:
        """
        if self.serial:
            self.serial.write(str)
        else:
            print "Serial is not initialized"

    def read(self, size=1):
        """
        Read n bytes from serial.

        :param size: number of bytes read from serial
        :return: data read from serial.
        """
        if self.serial:
            data = self.serial.read(size=size)
            return data
        else:
            print "Serial is not initialized"

    def read_all(self):
        """
        Read all data on serial.

        :return: Byte representation of data on serial.
        """
        if self.serial:
            return self.read(size=self.serial.inWaiting())
        else:
            print "Serial is not initialized"

    def close(self):
        """
        Clean up and close serial port.

        :return:
        """
        self.serial.close()
        self.serial = None
