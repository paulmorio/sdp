from serial import Serial

# Command constants
MOVE_FORWARD = "FWD"
CRAWL_FORWARD = "CRAWL_F"
MOVE_BACK = "BACK"
CRAWL_BACK = "CRAWL_B"
TURN_LEFT = "TURN_L"
TURN_RIGHT = "TURN_R"
GRABBER_TOGGLE = "GRAB"
GRABBER_OPEN = "O_GRAB"
GRABBER_CLOSE = "C_GRAB"
GRABBER_DEFAULT = "C_GRAB"
SHOOT = "SHOOT"
PASS = "PASS"
STOP_DRIVE_MOTORS = "STOP_D"
STOP_ALL_MOTORS = "STOP_A"
MOTOR_TEST = "MOTORS"
READY = "READY"
COMMAND_TERMINAL = '\n'


class Robot(object):
    """Serial connection setup, IO, and robot actions."""

    def __init__(self, port="/dev/ttyACM0", timeout=0.05,
                 rate=115200, comms=True):
        """
        Create a robot object which provides action methods and opens a serial
        connection.

        :param port: Default is "/dev/ttyACM0". This changes based on
        platform, etc. The default should correspond to what shows on the DICE
        machines.
        :param timeout: Serial read timeout - used for alternating bit protocol.
        :param rate: Baud rate
        :param comms: If true then start serial comms.
        :return: Robot object
        """
        self.last_command = None
        self.ready = False
        if comms:
            self.ack_bit = '0'
            self.serial = Serial(port, rate, timeout=timeout)
            self.command(READY)
            self.ready = True

        else:
            self.serial = None
            self.ready = True

    def command(self, command, arguments=[]):
        """
        Send a command to the robot then wait for acknowledgement. Resend
        the command if no acknowledgement is received within the serial read
        timeout.

        :param command: The command to be sent. This should be one of the
        constants defined within this module.
        :param arguments: Optional arguments to be appended to the command.
        """
        if self.serial is not None:
            self.last_command = command

            # Append alternating bit and given arguments
            self.last_command += ' ' + self.ack_bit
            for arg in arguments:
                self.last_command += ' ' + arg

            # Append terminal char, wait for acknowledgement
            self.serial.write(command + COMMAND_TERMINAL)
            self.ack()
        else:
            #print command
            pass

    def close(self):
        """
        Teardown sequence. Stop robot motors, set grabber to default position,
        then close the serial port
        """
        if self.serial is not None:
            self.command(STOP_ALL_MOTORS)
            self.command(GRABBER_CLOSE)
            self.serial.close()
            print "Robot teardown complete. Serial connection is closed."

    def ack(self):
        """
        Wait for the robot to acknowledge the most recent command. Resend
        this command if no acknowledgement is received within the serial port
        timeout.
        """
        ack = self.serial.readline()  # returns empty string on timeout
        if ack != '' and ack[0] == self.ack_bit:  # Successful ack
            if self.ack_bit == '1':
                self.ack_bit = '0'
            else:
                self.ack_bit = '1'
        else:  # No ack within timeout - resend command
            self.command(self.last_command)


class ManualController(object):
    """
    A graphical window which provides manual control of the robot. This
    allows for easy partial testing of the robot's actions.

    Note that this requires that the manualcontrol sketch is loaded on the
    Arduino.

    See manual_controls.txt for controls.
    """

    robot = None

    def __init__(self, port="/dev/ttyACM0", rate=115200):
        """
        :param port: Serial port to be used. Default is fine for DICE
        :param rate: Baudrate. Default is 115200
        :return: ManualController object.
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
        self.root.bind('w', lambda event: self.robot.command(MOVE_FORWARD))
        self.root.bind('<Up>', lambda event: self.robot.command(CRAWL_FORWARD))
        self.root.bind('x', lambda event: self.robot.command(MOVE_BACK))
        self.root.bind('<Down>', lambda event: self.robot.command(CRAWL_BACK))
        self.root.bind('<Left>', lambda event: self.robot.command(TURN_LEFT))
        self.root.bind('<Right>', lambda event: self.robot.command(TURN_RIGHT))
        self.root.bind('a', lambda event: self.robot.command(TURN_LEFT))
        self.root.bind('d', lambda event: self.robot.command(TURN_RIGHT))
        self.root.bind('g', lambda event: self.robot.command(GRABBER_TOGGLE))
        self.root.bind('o', lambda event: self.robot.command(GRABBER_OPEN))
        self.root.bind('c', lambda event: self.robot.command(GRABBER_CLOSE))
        self.root.bind('<space>', lambda event: self.robot.command(SHOOT))
        self.root.bind('v', lambda event: self.robot.command(PASS))
        self.root.bind('s', lambda event: self.robot.command(STOP_DRIVE_MOTORS))
        self.root.bind('<Escape>', lambda event: self.quit())

        # Set window attributes and start
        self.root.geometry('400x400')
        self.root.wm_title("Manual Control")
        self.root.wm_attributes("-topmost", 1)
        self.root.mainloop()
        self.root.protocol('WM_DELETE_WINDOW', self.quit)

    def quit(self):
        """
        Initialise robot teardown then destroy window.
        """
        self.robot.close()
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