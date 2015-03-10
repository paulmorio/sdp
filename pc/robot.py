from serial import Serial
import math
import threading
import time

# Command string constants
_DRIVE = "DRIVE"
_OPEN_GRABBER = "O_GRAB"
_CLOSE_GRABBER = "C_GRAB"
_KICK = "KICK"
_READY = "READY"
_STATUS = "STATUS"
_COMM_DELIMITER = ' '
_COMM_TERMINAL = '\n'

_UPDATE_FREQ = 100  # How often (in ms) we may update state (prevents flooding)

# Robot constants
_ROTARY_SENSOR_RESOLUTION = 2.0
_WHEEL_DIAM_CM = 8.16
_TICK_DIST_CM = math.pi * _WHEEL_DIAM_CM * _ROTARY_SENSOR_RESOLUTION / 360.0
_WHEELBASE_DIAM_CM = 10.93
_WHEELBASE_CIRC_CM = _WHEELBASE_DIAM_CM * math.pi


class Robot(object):
    """
    Serial connection, IO, and robot actions.
    """

    def __init__(self, port="/dev/ttyACM0", timeout=0.1,
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
        self._current_command = None
        self.ready = False  # True if ready to receive a command
        self.grabber_open = True
        self.is_grabbing = False
        self.is_moving = False
        self.is_kicking = False
        self.ball_grabbed = False
        self.last_state_update = time.time()*1000 - _UPDATE_FREQ
        self.waiting_for_ack = False

        if comms:
            t = threading.Thread(target=self.ack_listener)
            t.daemon = True
            t.start()
            self._ack_bit = '0'
            self._serial = Serial(port, rate, timeout=timeout)
            self._initialize()
        else:
            self._serial = None
            self.ready = True
            self._ack_bit = '0'

    @property
    def current_command(self):
        if self._current_command is not None:
            cmd, args = self._current_command
            if args is not None:  # Append arguments
                for arg in args:
                    cmd += _COMM_DELIMITER + arg
            cmd += _COMM_DELIMITER + self._ack_bit  # Append ack bit
            cmd += _COMM_TERMINAL  # Append terminal
            return cmd
        else:
            return None

    @current_command.setter
    def current_command(self, val):
        """
        Set the current command.
        :param val: Iterable/tuple - cmd [args]
        :return:
        """
        try:
            cmd, args = val
        except ValueError:
            raise ValueError("Pass an iterable (cmd, [args])")
        else:
            self._current_command = cmd, args

    def reset_command(self):
        """
        Set the current command to None. Used by the ack thread once a command
        has been deemed successful.
        """
        self._current_command = None

    def _command(self):
        """
        Send a command to the robot then wait for acknowledgement. Resend
        the command if no acknowledgement is received within the serial read
        timeout.

        send the current command to the robot
        """
        if self.current_command is not None:
            # Send and wait for ack
            if self._serial is not None:
                self._serial.write(self.current_command)
                self._serial.flush()
                self.waiting_for_ack = True
            else:
                print self.current_command

    def _initialize(self):
        """
        Initialize the robot: set the grabber to the default position then wait
        for acknowledgement before setting the ready flag.
        """
        while self.grabber_open:
            if not self.is_grabbing:
                self.close_grabber()
            else:
                self.update_state()
        self.ready = True

    def drive(self, l_dist, r_dist, l_power=60, r_power=60):
        """
        Drive the robot for the giving left and right wheel distances at the
        given powers. There is some loss of precision as the unit of distance
        is converted into rotary encoder 'ticks'.

        To stop a drive motor you can give a 0 argument for distance or power.

        :param l_dist: Distance travelled by the left wheel in centimetres. A
        negative value runs the motor in reverse (drive backward).
        :type l_dist: float
        :param r_dist: Distance travelled by the right wheel in centimetres. A
        negative value runs the motor in reverse (drive backward).
        :type r_dist: float
        :param l_power: Motor power from 0-100 - note that low values may not
        provide enough torque for movement.
        :type l_power: int
        :param r_power: Motor power from 0-100 - low values may not provide
        enough torque for drive.
        """
        # Currently rounding down strictly as too little is better than too much
        cm_to_ticks = lambda cm: int(cm / _TICK_DIST_CM)
        l_dist = str(cm_to_ticks(l_dist))
        r_dist = str(cm_to_ticks(r_dist))
        self.current_command = \
            (_DRIVE, [l_dist, r_dist, str(l_power), str(r_power)])

    def stop(self):
        """
        Stop the robot's drive motors.
        """
        self.drive(0, 0)

    def turn(self, radians, power=60):
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
        wheel_dist = _WHEELBASE_CIRC_CM * radians / (2 * math.pi)
        self.drive(wheel_dist, -wheel_dist, power, power)

    def open_grabber(self, time=250, power=100):
        """
        Run the grabber motor in the opening direction for the given number of
        milliseconds at the given motor power.

        :param time: Time to run the motor in milliseconds.
        :type time: int
        :param power: Motor power from 0-100
        :type power: int
        """
        self.current_command = (_OPEN_GRABBER, [str(time), str(power)])

    def close_grabber(self, time=250, power=100):
        """
        Run the grabber motor in the closing direction for the given number of
        milliseconds at the given motor power.

        :param time: Time to run the motor in milliseconds.
        :type time: int
        :param power: Motor power from 0-100
        :type power: int
        """
        self.current_command = (_CLOSE_GRABBER, [str(time), str(power)])

    def kick(self, time=600, power=100):
        """
        Run the kicker motor forward for the given number of milliseconds at the
        given motor speed.

        :param time: Time to run the motor in milliseconds
        :type time: int
        :param power: Motor power from 0-100
        :type power: int
        """
        self.current_command = (_KICK, [str(time), str(power)])

    def teardown(self):
        """
        Stop robot motors, set grabber to default position, then close the
        serial port.
        """
        if self._serial is not None:
            while self.is_moving:
                self.stop()  # Stop drive motors
            while self.grabber_open:
                if self.is_grabbing:
                    self.update_state()
                else:
                    self.close_grabber()
            self._serial.flush()
            self._serial.close()
            print "Robot teardown complete. Serial connection is closed."

    def update_state(self):
        """
        Dummy action to get an ack with updated state from the bot.
        """
        current_time_ms = time.time()*1000
        if not self.ready \
                or current_time_ms >= self.last_state_update + _UPDATE_FREQ:
            self.last_state_update = current_time_ms
            self.current_command = (_STATUS, [])

    def ack_listener(self):
        """
        Listener for acks and status updates.

        Wait for the robot to acknowledge the most recent command. Resend
        this command if no acknowledgement is received within the serial port
        timeout.

        The acknowledge packet is of the following format:
        [ack_bit][grabber_open][is_grabbing][is_moving][is_kicking]
        """
        while True:
            if self.waiting_for_ack:
                ack = self._serial.readline()
                if len(ack) == 8 and ack[0] == self._ack_bit:  # Successful ack
                    self._ack_bit = '1' if self._ack_bit == '0' else '0'  # Flip
                    self.grabber_open = ack[1] == '1'
                    self.is_grabbing = ack[2] == '1'
                    self.is_moving = ack[3] == '1'
                    self.is_kicking = ack[4] == '1'
                    self.ball_grabbed = ack[5] == '1'

                    self.waiting_for_ack = False
                    self.reset_command()
                else:
                    # Ack failed, send command again
                    self._command()
            elif self.current_command is not None:
                # New command
                self._command()


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
        self.root.bind('<Down>', lambda event: self.robot.drive(-20, -20,
                                                                70, 70))
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