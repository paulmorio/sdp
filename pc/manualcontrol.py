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
        root.bind('q', self.bot.left_strafe_toggle)
        root.bind('e', self.bot.right_strafe_toggle)
        root.bind('w', self.bot.forward_toggle)
        root.bind('s', self.bot.back_toggle)
        root.bind('a', self.bot.turn_left_90)
        root.bind('d', self.bot.turn_right_90)
        root.bind('g', self.bot.grab_toggle)
        root.bind('<space>', self.bot.kick)
        root.bind('t', self.bot.run_motors)

        # Set window attributes and start
        # TODO force proper focus on new window. root.focus_force insufficient
        root.geometry('300x200')
        root.wm_title("Manual Control")
        root.wm_attributes("-topmost", 1)
        root.mainloop()
