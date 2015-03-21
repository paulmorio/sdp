import math
from multiprocessing import Process, Pipe

from pc.comms.communicator import Communicator


# Command string constants
DRIVE = "DRIVE"
OPEN_GRABBER = "O_GRAB"
CLOSE_GRABBER = "C_GRAB"
KICK = "KICK"
READY = "READY"
STATUS = "STATUS"
CMD_DELIMITER = ' '

# Robot constants
ROTARY_SENSOR_RESOLUTION = 2.0
WHEEL_DIAM_CM = 8.16
TICK_DIST_CM = math.pi * WHEEL_DIAM_CM * ROTARY_SENSOR_RESOLUTION / 360.0
WHEELBASE_DIAM_CM = 10.93
WHEELBASE_CIRC_CM = WHEELBASE_DIAM_CM * math.pi


class Robot(object):
    """
    Robot actions and feedback.
    """

    def __init__(self, port="/dev/ttyACM0", comms=True):
        """
        Create a robot object which provides action methods and robot feedback.

        :param port: Default is "/dev/ttyACM0". This changes based on
        platform, etc. The default should correspond to what shows on the DICE
        machines.
        :param comms: Whether to communicate with the robot.
        """

        self._queued_command = None  # Next command to be sent
        self.waiting_for_ack = False  # Waiting for update from communicator
        self.ready = False  # True if ready to receive a command
        self.grabber_open = True  # Assume open
        self.is_grabbing = False  # Performing a grab
        self.is_moving = False  # Performing a drive/turn
        self.is_kicking = False  # Kick motor is running
        self.ball_grabbed = False  # Ball sensor is pressed
        self.comms = comms

        if self.comms:
            # Start communicator subprocess
            self.comm_pipe, sub_pipe = Pipe()
            comm = Communicator(sub_pipe, port)
            self.p = Process(target=comm.runner)
            self.p.start()
            self._initialize()

    @property
    def queued_command(self):
        if self._queued_command is not None:
            cmd, arguments = self._queued_command
            for arg in arguments:
                cmd += CMD_DELIMITER + arg
            return cmd
        else:
            return None

    @queued_command.setter
    def queued_command(self, val):
        """
        Set the current command. Can only set if it is currently none.
        :param val: Iterable/tuple - cmd [args]
        """
        try:
            cmd, arguments = val
        except ValueError:
            raise ValueError("Pass an iterable (cmd, [args])")
        else:
            self._queued_command = cmd, arguments

    def reset_queued_command(self):
        self._queued_command = None

    def act(self):
        """
        If we're waiting for an ack then poll and deal with it. Otherwise
        send the queued command.

        If comms is false then just print the queued command and clear it.
        """
        if self.waiting_for_ack:
            if self.comm_pipe.poll():
                state_str = self.comm_pipe.recv()
                self._update_state_bits(state_str)
                self.waiting_for_ack = False

        elif self.queued_command is not None:  # There is a queued command
            if self.comms:
                self.comm_pipe.send(self.queued_command)
                self.waiting_for_ack = True
                self.reset_queued_command()
            else:
                print self.queued_command
                self.reset_queued_command()

        elif self.ready:  # If there is no queued command, request state update
            self.update_state()
        # TODO return state to caller for passing to world

    def _update_state_bits(self, string):
        """
        Given the state part of an ack string, update the robot's state bits.
        :param string: State part of an ack string received from the robot.
        """
        self.grabber_open = string[0] == '1'
        self.is_grabbing = string[1] == '1'
        self.is_moving = string[2] == '1'
        self.is_grabbing = string[3] == '1'
        self.is_kicking = string[4] == '1'
        self.ball_grabbed = string[5] == '1'

    def _initialize(self):
        """
        Initialize the robot: set the grabber to the default position then wait
        for acknowledgement before setting the ready flag.
        """
        while self.grabber_open:
            self.act()  # No planner initialized to do this right now
            if not self.is_grabbing:
                self.close_grabber()
            else:
                self.update_state()
        self.ready = True

    def teardown(self):
        """
        Stop robot motors, set grabber to default position, then close the
        serial port.

        Note that we have act calls in here in case the higher level has stopped
        calling act (usually the case as this is called once the planner is
        done.
        """
        while True:
            # Stop movement
            if self.is_moving:
                self.stop()  # Stop drive motors

            # Close grabber
            elif self.grabber_open:
                if self.is_grabbing:
                    self.update_state()
                else:
                    self.close_grabber()

            # Robot is stopped and grabber is closed, we're done
            else:
                break

            # Run command
            self.act()

        self.p.terminate()  # Stop subprocess
        print "Robot teardown complete."

    def update_state(self):
        """
        Dummy action to get an ack with updated state from the bot.
        """
        self.queued_command = (STATUS, [])

    def drive(self, l_dist, r_dist, l_power=100, r_power=100):
        """
        Drive the robot for the giving left and right wheel distances at the
        given powers. There is some loss of precision as the unit of distance
        is converted into rotary encoder 'ticks'.

        To stop a drive motor you can give a 0 argument for distance or power.

        :param l_dist: Distance travelled by the left wheel in centimetres. A
        negative value runs the motor in reverse (drive backward).
        :param r_dist: Distance travelled by the right wheel in centimetres. A
        negative value runs the motor in reverse (drive backward).
        :param l_power: Motor power from 0-100 - note that low values may not
        provide enough torque for movement.
        :param r_power: Motor power from 0-100 - low values may not provide
        enough torque for drive.
        """
        # Currently rounding down strictly as too little is better than too much
        cm_to_ticks = lambda cm: int(cm / TICK_DIST_CM)
        l_dist = str(cm_to_ticks(l_dist))
        r_dist = str(cm_to_ticks(r_dist))
        self.queued_command = \
            (DRIVE, [l_dist, r_dist, str(l_power), str(r_power)])

    def stop(self):
        """
        Stop the robot's drive motors.
        """
        self.drive(0, 0)

    def turn(self, radians, power=100):
        """
        Turn the robot at the given motor power. The radians should be relative
        to the current orientation of the robot, where the robot is facing 0 rad
        and radians in (0,inf) indicate a rightward turn while radians in
        (-inf,-0) indicate a leftward turn.

        :param radians: Radians to turn from current orientation. Sign indicates
                        direction (negative -> leftward, positive -> rightward)
        :param power: Motor power
        """
        wheel_dist = WHEELBASE_CIRC_CM * radians / (2 * math.pi)
        self.drive(wheel_dist, -wheel_dist, power, power)

    def open_grabber(self, time=250, power=100):
        """
        Run the grabber motor in the opening direction for the given number of
        milliseconds at the given motor power.

        :param time: Time to run the motor in milliseconds.
        :param power: Motor power from 0-100
        """
        self.queued_command = (OPEN_GRABBER, [str(time), str(power)])

    def close_grabber(self, time=250, power=100):
        """
        Run the grabber motor in the closing direction for the given number of
        milliseconds at the given motor power.

        :param time: Time to run the motor in milliseconds.
        :param power: Motor power from 0-100
        """
        self.queued_command = (CLOSE_GRABBER, [str(time), str(power)])

    def kick(self, time=600, power=100):
        """
        Run the kicker motor forward for the given number of milliseconds at the
        given motor speed.

        :param time: Time to run the motor in milliseconds
        :param power: Motor power from 0-100
        """
        self.queued_command = (KICK, [str(time), str(power)])


class ManualController(object):
    """
    A graphical window which provides manual control of the robot. This
    allows for easy partial testing of the robot's actions.

    Note that this requires that the manualcontrol sketch is loaded on the
    Arduino.

    See manual_controls.txt for controls.
    """

    def __init__(self, port="/dev/ttyACM0"):
        """
        :param port: Serial port to be used. Default is fine for DICE
        """
        self.robot = Robot(port)
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
        self.root.bind('w', lambda event: self.robot.drive(10, 10))
        self.root.bind('<Up>', lambda event: self.robot.drive(20, 20, 70, 70))
        self.root.bind('x', lambda event: self.robot.drive(-10, -10))
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

        self.root.after(1, self.run_comms_loop)  # Run comms update in loop

        self.root.mainloop()

    def run_comms_loop(self):
        self.robot.act()
        self.root.after(1, self.run_comms_loop)

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