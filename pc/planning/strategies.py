from utilities import *
import math


class Strategy(object):
    """
    A base class on which other strategies should be built. Sets up the
    interface used by the Planner class.
    """
    def __init__(self, world, robot_ctl, state_map):
        self.state_map = state_map
        self.world = world
        self.robot_ctl = robot_ctl
        self._state = self.state_map.keys()[0]
        self.robot_mdl = world.our_attacker
        self.ball = world.ball

    @property
    def state(self):
        """
        Current state of the strategy in play.
        :return: Strategy state.
        """
        return self._state

    @state.setter
    def state(self, new_state):
        """
        Set a new state.
        :param new_state: New state to be set. Must be valid else AssertionError
        """
        assert (new_state in self.state_map.keys())
        self._state = new_state

    def reset(self):
        """Reset the Strategy object to its initial state."""
        self._state = self.state_map.keys()[0]

    def final_state(self):
        """Return True if the current state is final."""
        return self._state == self.state_map.keys()[-1]

    def act(self):
        """Call the appropriate method given the state map and current state."""
        self.state_map[self.state]()

    def do_nothing(self):
        pass


class Idle(Strategy):
    """
    The idle strategy has the robot do nothing.
    Intended use is when the ball is not visible or not reachable by the robot.
    """
    def __init__(self):
        _STATE_MAP = {IDLE: self.do_nothing}
        super(Idle, self).__init__(None, None, _STATE_MAP)


class GetBall(Strategy):
    """
    Have the robot move to the ball then grab it.
    Intended use is when the ball is in our robot's area.
    """
    def __init__(self, world, robot_ctl):
        _STATE_MAP = {INIT: self.face_ball,
                      FACING_BALL: self.open_grabber,
                      GRABBER_OPEN: self.move_to_ball,
                      BALL_IN_GRABBER_AREA: self.grab_ball,
                      TESTING_GRAB: self.grab_test,
                      POSSESSION: self.do_nothing}
        super(GetBall, self).__init__(world, robot_ctl, _STATE_MAP)
        self.ball = self.world.ball
        self.grab_tested = False

    def face_ball(self):
        """
        Command the robot to turn to face the ball, transition when the angle
        difference is within an acceptable margin.
        """
        angle_to_ball = self.robot_mdl.get_rotation_to_point(self.ball.x,
                                                             self.ball.y)
        if not self.robot_ctl.is_moving:
            if abs(angle_to_ball) < ROTATE_MARGIN:
                self.state = FACING_BALL
            else:
                self.robot_ctl.turn(angle_to_ball)
        else:
            self.robot_ctl.update_state()

    def open_grabber(self):
        """
        Give the open grabber command, transition when the grabber is open.
        """
        if not self.robot_ctl.is_grabbing:
            if self.robot_ctl.grabber_open:
                self.state = GRABBER_OPEN
            else:
                self.robot_ctl.open_grabber()
        else:
            self.robot_ctl.update_state()

    def move_to_ball(self):
        """
        Command the robot to move to the ball, transition when the ball is
        within the robot grabber area.
        """
        if not self.robot_ctl.is_moving:
            if self.robot_mdl.can_catch_ball(self.ball):
                self.robot_ctl.stop()
                self.state = BALL_IN_GRABBER_AREA
            else:
                dist = self.robot_mdl.get_displacement_to_point(self.ball.x,
                                                                self.ball.y)
                self.robot_ctl.move(dist)
        else:
            self.robot_ctl.update_state()

    def grab_ball(self):
        """
        Command the robot to grab the ball, transition when the ball is grabbed
        and the grab test has been passed.
        """
        if not self.robot_ctl.is_grabbing:
            if not self.robot_ctl.grabber_open:
                self.robot_ctl.turn(math.pi)
                self.state = TESTING_GRAB
            else:
                self.robot_ctl.close_grabber()
        else:
            self.robot_ctl.update_state()

    def grab_test(self):
        """
        Have the robot do a half-turn and then check if the ball is still in
        the grabber.
        """
        if not self.robot_ctl.is_moving:
            if self.robot_mdl.can_catch_ball(self.ball):
                self.state = POSSESSION
            else:
                self.state = INIT
        else:
            self.robot_ctl.update_state()


class PassBall(Strategy):
    """
    Have the robot find a path and pass to the defending robot.
    Intended use is when the ball is in our possession.
    """
    def __init__(self, world, robot_ctl):
        _STATE_MAP = {INIT: self.do_nothing()}
        super(PassBall, self).__init__(world, robot_ctl, _STATE_MAP)
