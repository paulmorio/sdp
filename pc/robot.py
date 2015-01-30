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

        # Robot manual control actions - requires the manualcontrol sketch.
    def kick(self, event=None):
        """ Send kick signal to bot """
        self.bot.write("KICK\n")

    def strafe_left(self, event=None):
        """ Send left strafe signal to bot"""
        self.bot.write("ST_L\n")

    def strafe_right(self, event=None):
        """ Send right strafe signal to bot"""
        self.bot.write("ST_R\n")

    def strafe_fl(self, event=None):
        self.bot.write("ST_FL\n")

    def strafe_fr(self, event=None):
        self.bot.write("ST_FR\n")

    def strafe_bl(self, event=None):
        self.bot.write("ST_BL\n")

    def strafe_br(self, event=None):
        self.bot.write("ST_BR\n")

    def forward(self, event=None):
        """Send forward signal to bot"""
        self.bot.write("FWD\n")

    def backward(self, event=None):
        """Send backward signal to bot"""
        self.bot.write("BACK\n")

    def turn_left(self, event=None):
        """ Send turn left signal to bot"""
        self.bot.write("TURN_L\n")

    def turn_right(self, event=None):
        """Send turn right signal to bot"""
        self.bot.write("TURN_R\n")

    def stop_motors(self, event=None):
        """Send stop signal to bot"""
        self.bot.write("STOP\n")

    def run_motors(self, event=None):
        """Send run motors signal to bot - sanity test"""
        self.bot.write("MOTORS\n")