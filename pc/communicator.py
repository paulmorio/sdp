from serial import Serial


class Communicator(Serial):
    """
    Initialise serial connection to robot. Handles communication back and forth.
    """

    def __init__(self, port="/dev/ttyACM0", rate=115200, timeout=1):
        """
        Create a communicator which acts as an interface for serial
        communication.

        :param port: Default is "/dev/ttyACM0". This changes based on
        platform, etc. The default should correspond to what shows on the DICE
        machines.

        :param rate: Baud rate
        :param timeout: write timeout in seconds
        :return:
        """
        super(Communicator, self).__init__(port, rate, timeout=timeout)

    def read_all(self):
        """
        Read all data on serial.

        :return: Byte representation of data on serial.
        """
        return self.read(self.inWaiting())