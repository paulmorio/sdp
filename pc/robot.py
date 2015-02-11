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
READY = "READY"
COMMAND_TERMINAL = '\n'


class Robot(object):
    """Serial connection setup, IO, and robot actions."""

    def __init__(self, port="/dev/ttyACM0", timeout=0.01, rate=115200, comms=True):
        """
        Create a robot object which provides action methods and opens a serial
        connection.

        :param port: Default is "/dev/ttyACM0". This changes based on
        platform, etc. The default should correspond to what shows on the DICE
        machines.

        :param rate: Baud rate
        :return:
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
            self.last_command = command
            print "COMMAND ENTERED: "+str(command)
            self.serial.write(command + COMMAND_TERMINAL)
            self.ack()
        else:
            print command

    def close(self):
        """ Close the robot's serial port """
        if self.serial is not None:
            self.command(STOP_ALL_MOTORS)
            self.command(GRABBER_CLOSE)
            self.serial.close()
            print "Serial port closed."

    def ack(self):
        ack = None
        ack = self.serial.readline()
        if ack == '':
            self.command(self.last_command)
        elif ack[0] == self.ack_bit:
            self.ack_bit = '1' if self.ack_bit == '0' else '1'
            self.serial.flushInput()


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
        self.root.bind('a', lambda event: self.robot.command(TURN_LEFT))
        self.root.bind('d', lambda event: self.robot.command(TURN_RIGHT))
        self.root.bind('o', lambda event: self.robot.command(GRABBER_OPEN))
        self.root.bind('c', lambda event: self.robot.command(GRABBER_CLOSE))
        self.root.bind('<space>', lambda event: self.robot.command(SHOOT))
        self.root.bind('v', lambda event: self.robot.command(PASS))
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