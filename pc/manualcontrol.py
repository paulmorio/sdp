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
        controls_file.close()

        # Compose window elements
        root = tk.Tk()
        text = tk.Label(root, background='white', text=controls)
        text.pack()

        # Set up key bindings
        root.bind('w', lambda event: self.bot.forward())
        root.bind('x', lambda event: self.bot.backward())
        root.bind('a', lambda event: self.bot.strafe_left())
        root.bind('d', lambda event: self.bot.strafe_right())
        root.bind('s', lambda event: self.bot.stop_motors())
        root.bind('<space>', lambda event: self.bot.kick())
        root.bind('<Left>', lambda event: self.bot.turn_left())
        root.bind('<Right>', lambda event: self.bot.turn_right())
        root.bind('t', lambda event: self.bot.run_motors())

        # Set window attributes and start
        root.geometry('300x400')
        root.wm_title("Manual Control")
        root.wm_attributes("-topmost", 1)
        root.mainloop()


# TODO: add no-comms option for testing
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("port", help="DICE /dev/ttyACM0")

    args = parser.parse_args()
    controller = ManualControl(port=args.port)
    controller.start()