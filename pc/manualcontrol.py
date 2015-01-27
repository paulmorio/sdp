import Tkinter as tk
import robot


class ManualControl():
    """
    A graphical window which provides manual control of the robot. This
    allows for easy partial testing of the robot's actions.

    See manual_controls.txt for controls.
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
        warning = "Please ensure that the manualcontrol.ino sketch is loaded.\n"
        controls_file.close()

        # Compose window elements
        root = tk.Tk()
        text = tk.Label(root, background='white', text=(warning + controls))
        text.pack()

        # Set up key bindings
        root.bind('w', lambda event: self.forward())
        root.bind('x', lambda event: self.backward())
        root.bind('a', lambda event: self.strafe_left())
        root.bind('d', lambda event: self.strafe_right())
        root.bind('s', lambda event: self.stop_motors())
        root.bind('<space>', lambda event: self.kick())
        root.bind('<Left>', lambda event: self.turn_left())
        root.bind('<Right>', lambda event: self.turn_right())
        root.bind('t', lambda event: self.run_motors())
        root.bind('q', lambda event: self.strafe_fl())
        root.bind('e', lambda event: self.strafe_fr())
        root.bind('z', lambda event: self.strafe_bl())
        root.bind('c', lambda event: self.strafe_br())

        # Set window attributes and start
        root.geometry('300x400')
        root.wm_title("Manual Control")
        root.wm_attributes("-topmost", 1)
        root.mainloop()

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

# TODO: add no-comms option for testing
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("port", help="DICE /dev/ttyACM0")

    args = parser.parse_args()
    controller = ManualControl(port=args.port)
    controller.start()