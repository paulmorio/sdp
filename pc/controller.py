import Tkinter as tk
import robot
import planner

class Controller():
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
        planner = Planner(self.bot)

# TODO: add no-comms option for testing
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("port", help="DICE /dev/ttyACM0")

    args = parser.parse_args()
    controller = ManualControl(port=args.port)
    controller.start()