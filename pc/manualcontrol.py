import Tkinter as tk
import robot


class ManualControl():
    """
    A graphical window which provides manual control of the robot. This
    allows for easy partial testing of the robot's actions.
    """

    bot = None

    def __init__(self, port="/dev/ttyACM0", rate=115200, timeout=1):
        """

        :param port: Serial port to be used. Default is fine for DICE
        :param rate: Baudrate. Default is 115200
        :param timeout: Write timeout in seconds. Default is 1.
        :return: None
        """
        self.bot = robot.Robot(port=port, rate=rate, timeout=timeout)

    def start(self):
        # Grab control text from file
        controls_file = open("manual_controls.txt")
        controls = controls_file.read()
        controls_file.close()

        # Compose window elements
        root = tk.Tk()
        text = tk.Label(root, background='white', text=controls)
        text.pack()

        # Set up key bindings
        root.bind('q', self.left_strafe_toggle)
        root.bind('e', self.right_strafe_toggle)
        root.bind('w', self.forward_toggle)
        root.bind('s', self.back_toggle)
        root.bind('a', self.turn_left_90)
        root.bind('d', self.turn_right_90)
        root.bind('g', self.grab_toggle)
        root.bind('<space>', self.kick)
        root.bind('t', self.run_motors)

        # Set window attributes and start
        # TODO force proper focus on new window. root.focus_force insufficient
        root.geometry('300x200')
        root.wm_title("Manual Control")
        root.wm_attributes("-topmost", 1)
        root.mainloop()

    # Manual control actions. These methods exist to strip the event argument
    # passed by Tkinter binds.
    def kick(self, event):
        """ Send kick signal to bot """
        self.bot.kick()

    def grab_toggle(self, event):
        """ Send grabber toggle signal to bot """
        self.bot.grab_toggle()

    def left_strafe_toggle(self, event):
        """ Send left strafe toggle signal to bot"""
        self.bot.left_strafe_toggle()

    def right_strafe_toggle(self, event):
        """ Send right strafe toggle signal to bot"""
        self.bot.right_strafe_toggle()

    def forward_toggle(self, event):
        """Send forward toggle signal to bot"""
        self.bot.forward_toggle()

    def back_toggle(self, event):
        """Send back toggle signal to bot"""
        self.bot.back_toggle()

    def turn_left_90(self, event):
        """ Send signal to turn left 90deg"""
        self.bot.turn_left_90()

    def turn_right_90(self, event):
        """Send signal to turn right 90deg"""
        self.bot.turn_right_90()

    def run_motors(self, event):
        """Run motors to indicate that e.g. comms is working"""
        self.bot.run_motors()