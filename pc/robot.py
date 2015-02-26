from serial import Serial
import math


class Robot(object):
    """
    Serial connection, IO, and robot actions.
    """

    # Command string constants
    _DRIVE = "DRIVE"
    _OPEN_GRABBER = "O_GRAB"
    _CLOSE_GRABBER = "C_GRAB"
    _KICK = "KICK"
    _READY = "READY"
    _COMM_DELIMITER = ' '
    _COMM_TERMINAL = '\n'

    # Robot constants
    _ROTARY_SENSOR_RESOLUTION = 3.0
    _WHEEL_DIAM_CM = 8.16
    _TICK_DIST_CM = math.pi * _WHEEL_DIAM_CM * _ROTARY_SENSOR_RESOLUTION / 360.0
    _WHEELBASE_DIAM_CM = 10.93
    _WHEELBASE_CIRC_CM = _WHEELBASE_DIAM_CM * math.pi

    def __init__(self, port="/dev/ttyACM0", timeout=0.05,
                 rate=115200, comms=True):
        """
        Create a robot object which provides action methods and opens a serial
        connection.

        :param port: Default is "/dev/ttyACM0". This changes based on
        platform, etc. The default should correspond to what shows on the DICE
        machines.
        :type port: str
        :param timeout: Serial read timeout - used for alternating bit protocol.
        :type timeout: int
        :param rate: Baud rate
        :type rate: int
        :param comms: Whether to start serial communications.
        :type comms: bool
        :return: A robot object used to initialize the robot and send commands
        :rtype: Robot
        """
        self._last_command = None
        self.ready = False  # True if ready to receive a command
        self.grabber_open = False
        if comms:
            self._ack_bit = '0'
            self._serial = Serial(port, rate, timeout=timeout)
            self._initialize()
        else:
            self._serial = None
            self.ready = True
            self._ack_bit = '0'

    def _command(self, command, arguments=[]):
        """
        Send a command to the robot then wait for acknowledgement. Resend
        the command if no acknowledgement is received within the serial read
        timeout.

        :param command: The command to be sent. This should be one of the
        constants defined within this module.
        :type command: str
        :param arguments: Optional arguments to be appended to the command.
        :type arguments: list of str
        """
        # Store for resending
        self._last_command = (command, arguments)

        # Build the command
        current_command = command
        # Append alternating bit
        current_command += Robot._COMM_DELIMITER + self._ack_bit
        for arg in arguments:  # Append arguments
            current_command += Robot._COMM_DELIMITER + arg
        # Append terminal char
        current_command += Robot._COMM_TERMINAL
        # Send and wait for ack
        if self._serial is not None:
            self._serial.write(current_command)
            self._serial.flush()
            self.ack()
        else:
            print current_command

    def _initialize(self):
        """
        Initialize the robot: set the grabber to the default position then wait
        for acknowledgement before setting the ready flag.
        """
        self.close_grabber()
        self.ready = True

    def test(self):
        """
        Run the robot test sequence: spin a full rotation clockwise then counter
        clockwise, kick, open grabber, close grabber.
        """
        pass  # NYI

    def drive(self, l_dist, r_dist, l_power=100, r_power=100):
        """
        Drive the robot for the giving left and right wheel distances at the
        given powers. There is some loss of precision as the unit of distance
        is converted into rotary encoder 'ticks'.

        To stop a drive motor you can give a 0 argument for distance or power.

        :param l_dist: Distance travelled by the left wheel in centimetres. A
        negative value runs the motor in reverse (drive backward).
        :type l_dist: Float
        :param r_dist: Distance travelled by the right wheel in centimetres. A
        negative value runs the motor in reverse (drive backward).
        :type r_dist: Float
        :param l_power: Motor power from 0-100 - note that low values may not
        provide enough torque for movement.
        :type l_power: int
        :param r_power: Motor power from 0-100 - low values may not provide
        enough torque for drive.
        """
        # Currently rounding down strictly as too little is better than too much
        cm_to_ticks = lambda cm: int(cm / Robot._TICK_DIST_CM)
        l_dist = str(cm_to_ticks(l_dist))
        r_dist = str(cm_to_ticks(r_dist))
        self._command(Robot._DRIVE,
                      [l_dist, r_dist, str(l_power), str(r_power)])

    def turn(self, radians, power=100):
        """
        Turn the robot at the given motor power. The radians should be relative
        to the current orientation of the robot, where the robot is facing 0 rad
        and radians in (0,inf) indicate a rightward turn while radians in
        (-inf,-0) indicate a leftward turn.

        :param radians: Radians to turn from current orientation. Sign indicates
                        direction (negative -> leftward, positive -> rightward)
        :type radians: float
        :param power: Motor power
        :type power: int
        """
        wheel_dist = Robot._WHEELBASE_CIRC_CM * radians / (2 * math.pi)
        self.drive(wheel_dist, -wheel_dist, power, power)

    def open_grabber(self, time=1000, power=100):
        """
        Run the grabber motor in the opening direction for the given number of
        milliseconds at the given motor power.

        :param time: Time to run the motor in milliseconds.
        :type time: int
        :param power: Motor power from 0-100
        :type power: int
        """
        self._command(Robot._OPEN_GRABBER, [str(time), str(power)])
        self.grabber_open = True

    def close_grabber(self, time=1400, power=100):
        """
        Run the grabber motor in the closing direction for the given number of
        milliseconds at the given motor power.

        :param time: Time to run the motor in milliseconds.
        :type time: int
        :param power: Motor power from 0-100
        :type power: int
        """
        self._command(Robot._CLOSE_GRABBER, [str(time), str(power)])
        self.grabber_open = False

    def kick(self, time=700, power=100):
        """
        Run the kicker motor forward for the given number of milliseconds at the
        given motor speed.

        :param time: Time to run the motor in milliseconds
        :type time: int
        :param power: Motor power from 0-100
        :type power: int
        """
        self._command(Robot._KICK, [str(time), str(power)])

    def teardown(self):
        """
        Stop robot motors, set grabber to default position, then close the
        serial port
        """
        if self._serial is not None:
            self.drive(0, 0)  # Stop drive motors
            self.close_grabber()
            self._serial.flush()
            self._serial.close()
            print "Robot teardown complete. Serial connection is closed."

    def ack(self):
        """
        Wait for the robot to acknowledge the most recent command. Resend
        this command if no acknowledgement is received within the serial port
        timeout.

        The acknowledgement includes an alternating bit as well as some status
        bits as follows: [is_moving] [is_grabbing]
        """
        ack = self._serial.readline()  # returns empty string on timeout
        if ack != '' and ack[0] == self._ack_bit:  # Successful ack
            self._ack_bit = '0' if self._ack_bit == '1' else '0'
        else:  # No ack within timeout - resend command
            self._command(self._last_command[0], self._last_command[1])


class ManualController(object):
    """
    A graphical window which provides manual control of the robot. This
    allows for easy partial testing of the robot's actions.

    Note that this requires that the manualcontrol sketch is loaded on the
    Arduino.

    See manual_controls.txt for controls.
    """

    def __init__(self, port="/dev/ttyACM0", rate=115200):
        """
        :param port: Serial port to be used. Default is fine for DICE
        :type port: str
        :param rate: Baudrate. Default is 115200
        :type rate: int
        :return: A manualcontroller with an initialised robot object
        :rtype: ManualController
        """
        self.robot = Robot(port=port, rate=rate)
        self.root = None

    def start(self):
        """
        Create a tkinter GUI window to show manual controls and capture keys.
        """
        import Tkinter as tk
        import os
        # Grab control text from file
        script_dir = os.path.dirname(os.path.realpath(__file__))
        controls_file = open(os.path.join(script_dir, "manual_controls.txt"))
        controls = controls_file.read()
        controls_file.close()

        # Compose window elements
        self.root = tk.Tk()
        text = tk.Label(self.root, background='white', text=controls)
        text.pack()

        # Set up key bindings
        self.root.bind('w', lambda event: self.robot.drive(20, 20))
        self.root.bind('<Up>', lambda event: self.robot.drive(20, 20, 70, 70))
        self.root.bind('x', lambda event: self.robot.drive(-20, -20))
        self.root.bind('<Down>', lambda event: self.robot.drive(-20, -20, 70, 70))
        self.root.bind('<Left>', lambda event: self.robot.turn(-math.pi))
        self.root.bind('<Right>', lambda event: self.robot.turn(math.pi))
        self.root.bind('a', lambda event: self.robot.turn(-math.pi))
        self.root.bind('d', lambda event: self.robot.turn(math.pi))
        self.root.bind('o', lambda event: self.robot.open_grabber())
        self.root.bind('c', lambda event: self.robot.close_grabber())
        self.root.bind('<space>', lambda event: self.robot.kick())
        self.root.bind('s', lambda event: self.robot.drive(0, 0))
        self.root.bind('<Escape>', lambda event: self.quit())

        # Set window attributes and start
        self.root.geometry('400x400')
        self.root.wm_title("Manual Control")
        self.root.wm_attributes("-topmost", 1)
        self.root.mainloop()

    def quit(self):
        """
        Start robot teardown then destroy window.
        """
        self.robot.teardown()
        self.root.quit()


# Create a manualcontroller if robot.py is run from main
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("port",
                        help="Serial port to use - DICE is /dev/ttyACM0")
    args = parser.parse_args()
    controller = ManualController(port=args.port)
    controller.start()