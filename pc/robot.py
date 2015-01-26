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

    # Robot actions
    def kick(self):
        """ Send kick signal to bot """
        self.write("KICK\n")

    def strafe_left(self):
        """ Send left strafe signal to bot"""
        self.write("ST_L\n")

    def strafe_right(self):
        """ Send right strafe signal to bot"""
        self.write("ST_R\n")

    def forward(self):
        """Send forward signal to bot"""
        self.write("FWD\n")

    def backward(self):
        """Send backward signal to bot"""
        self.write("BACK\n")

    def turn_left(self):
        """ Send turn left signal to bot"""
        self.write("TURN_L\n")

    def turn_right(self):
        """Send turn right signal to bot"""
        self.write("TURN_R\n")

    def stop_motors(self):
        """Send stop signal to bot"""
        self.write("STOP\n")

    def run_motors(self):
        """Send run motors signal to bot - sanity test"""
        self.write("MOTORS\n")