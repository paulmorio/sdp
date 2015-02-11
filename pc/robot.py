from serial import Serial

# Command constants
MOVE_FORWARD = "FWD"
CRAWL_FORWARD = "CRAWL_F"
MOVE_BACK = "BACK"
CRAWL_BACK = "CRAWL_B"
TURN_LEFT = "TURN_L"
TURN_RIGHT = "TURN_R"
STRAFE_LEFT = "ST_L"
STRAFE_RIGHT = "ST_R"
STRAFE_FWD_LEFT = "ST_FL"
STRAFE_FWD_RIGHT = "ST_FR"
STRAFE_BACK_LEFT = "ST_BL"
STRAFE_BACK_RIGHT = "ST_BR"
GRABBER_TOGGLE = "GRAB"
GRABBER_OPEN = "O_GRAB"
GRABBER_CLOSE = "C_GRAB"
SHOOT = "SHOOT"
PASS = "PASS"
STOP_DRIVE_MOTORS = "STOP_D"
STOP_ALL_MOTORS = "STOP_A"
MOTOR_TEST = "MOTORS"
COMMAND_TERMINAL = '\n'


class Robot(object):
    """Serial connection setup, IO, and robot actions."""

    def __init__(self, port="/dev/ttyACM0", timeout=1, rate=115200, comms=True):
        """
        Create a robot object which provides action methods and opens a serial
        connection.

        :param port: Default is "/dev/ttyACM0". This changes based on
        platform, etc. The default should correspond to what shows on the DICE
        machines.

        :param rate: Baud rate
        :return:
        """
        if comms:
            self.serial = Serial(port, rate, timeout=timeout)
        else:
            self.serial = None

    # Serial communication methods
    def read_all(self):
        """
        Read all data from serial.

        :return: Byte representation of data on serial.
        """
        if self.serial:
            return self.serial.read(self.serial.inWaiting())
        else:
            print "No comms!"

    def command(self, command):
        """Append command terminal to string before writing to serial"""
        if self.serial is not None:
            print "COMMAND ENTERED: "+str(command)
            self.serial.write(command + COMMAND_TERMINAL)
        else:
            print command

    def close(self):
        """ Close the robot's serial port """
        if self.serial is not None:
            self.command(STOP_ALL_MOTORS)
            self.command(GRABBER_CLOSE)
            self.serial.close()
            print "Serial port closed."


class ManualController(object):
    """
    A graphical window which provides manual control of the robot. This
    allows for easy partial testing of the robot's actions.

    See manual_controls.txt for controls.
    """

    robot = None

    def __init__(self, port="/dev/ttyACM0", rate=115200):
        """
        :param port: Serial port to be used. Default is fine for DICE
        :param rate: Baudrate. Default is 115200
        :return: None
        """
        self.robot = Robot(port=port, rate=rate)
        self.root = None

    def start(self):
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
        self.root.bind('a', lambda event: self.robot.command(STRAFE_LEFT))
        self.root.bind('d', lambda event: self.robot.command(STRAFE_RIGHT))
        self.root.bind('q', lambda event: self.robot.command(STRAFE_FWD_LEFT))
        self.root.bind('e', lambda event: self.robot.command(STRAFE_FWD_RIGHT))
        self.root.bind('z', lambda event: self.robot.command(STRAFE_BACK_LEFT))
        self.root.bind('c', lambda event: self.robot.command(STRAFE_BACK_RIGHT))
        self.root.bind('g', lambda event: self.robot.command(GRABBER_TOGGLE))
        self.root.bind('<space>', lambda event: self.robot.command(SHOOT))
        self.root.bind('v', lambda event: self.robot.command(PASS))
        self.root.bind('t', lambda event: self.robot.command(MOTOR_TEST))
        self.root.bind('s', lambda event: self.robot.command(STOP_DRIVE_MOTORS))
        self.root.bind('<Escape>', self.quit)

        # Set window attributes and start
        self.root.geometry('400x400')
        self.root.wm_title("Manual Control")
        self.root.wm_attributes("-topmost", 1)
        self.root.mainloop()

    def quit(self, event):
        self.robot.close()
        self.root.quit()


# Create a manualcontroller if robot.py is run from main
# TODO: add no-comms option for testing
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("port", help="DICE /dev/ttyACM0")

    args = parser.parse_args()
    controller = ManualController(port=args.port)
    controller.start()