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
        self.write("A_KICK\n")

    def grab_toggle(self):
        """ Send grabber toggle signal to bot """
        self.write("A_GRAB\n")

    def left_strafe_toggle(self):
        """ Send left strafe toggle signal to bot"""
        self.write("A_L_ST\n")

    def right_strafe_toggle(self):
        """ Send right strafe toggle signal to bot"""
        self.write("A_R_ST\n")

    def forward_toggle(self):
        """Send forward toggle signal to bot"""
        self.write("A_FWD\n")

    def back_toggle(self):
        """Send back toggle signal to bot"""
        self.write("A_BK\n")

    def turn_left_90(self):
        """ Send signal to turn left 90deg"""
        self.write("A_TL_90\n")

    def turn_right_90(self):
        """Send signal to turn right 90deg"""
        self.write("A_TR_90\n")

    def run_motors(self):
        """Run motors to indicate that e.g. comms is working"""
        self.write("A_MTR\n")