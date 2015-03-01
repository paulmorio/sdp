from utilities import *
import math


class Strategy(object):
    """
    A base class on which other strategies should be built. Sets up the
    interface used by the Planner class.
    """
    def __init__(self, world, robot_ctl, states, state_map):
        self.states = states
        self.state_map = state_map
        self.world = world
        self.robot_ctl = robot_ctl
        self._state = self.states[0]
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
        assert (new_state in self.states)
        if new_state != self._state:
            self.robot_ctl.stop()
        self._state = new_state

    def transition(self):
        pass

    def reset(self):
        """Reset the Strategy object to its initial state."""
        self.state = self.states[0]

    def final_state(self):
        """Return True if the current state is final."""
        return self._state == self.states[-1]

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
    def __init__(self, world, robot_ctl):
        _STATES = [IDLE]
        _STATE_MAP = {IDLE: self.do_nothing}
        super(Idle, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)


class GetBall(Strategy):
    """
    Have the robot move to the ball then grab it.
    Intended use is when the ball is in our robot's area.
    """
    def __init__(self, world, robot_ctl):
        _STATES = [NOT_FACING_BALL, FACING_BALL, GRABBER_OPEN,
                   BALL_IN_GRABBER_AREA, TESTING_GRAB, POSSESSION]
        _STATE_MAP = {NOT_FACING_BALL: self.face_ball,
                      FACING_BALL: self.move_to_ball,
                      GRABBING_BALL: self.grab_ball,
                      POSSESSION: self.do_nothing}
        super(GetBall, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.ball = self.world.ball
        self.grab_tested = False
        self.grab_successful = False

    def transition(self):
        if self.grab_successful:
            self.state = POSSESSION
        elif not self.facing_ball():
            self.state = NOT_FACING_BALL
        elif not self.robot_mdl.can_catch_ball(self.world.ball):
            self.state = FACING_BALL
        elif self.robot_mdl.grabber_open:
            self.state = GRABBING_BALL
        elif not self.grab_tested:
            self.state = TESTING_GRAB
        # Else the ball has disappeared??

    def facing_ball(self):
        ball = self.world.ball
        angle_to_ball = self.robot_mdl.get_rotation_to_point(ball.x, ball.y)
        return -ROTATE_MARGIN < angle_to_ball < ROTATE_MARGIN

    def face_ball(self):
        """
        Command the robot to turn to face the ball.
        """
        self.grab_tested = False
        angle_to_ball = self.robot_mdl.get_rotation_to_point(self.ball.x,
                                                                 self.ball.y)
        self.robot_ctl.turn(angle_to_ball, 80)

    def move_to_ball(self):
        """
        Command the robot to move to the ball.
        """
        self.grab_tested = False
        if not self.robot_ctl.grabber_open:
            self.robot_ctl.open_grabber()
        dist = self.robot_mdl.get_displacement_to_point(self.ball.x,
                                                        self.ball.y)
        self.robot_ctl.drive(px_to_cm(dist), px_to_cm(dist))

    def grab_ball(self):
        """
        Command the robot to grab the ball. Test the grab
        """
        if self.grab_tested:
            self.grab_successful = True
        elif not self.robot_ctl.grabber_open:
            self.robot_ctl.turn(math.pi)
            self.grab_tested = True
        else:
            self.robot_ctl.close_grabber()


class PassBall(Strategy):
    """
    Have the robot find a path and pass to the defending robot.
    Intended use is when the ball is in our possession.
    """
    def __init__(self, world, robot_ctl):
        _STATES = [NOT_FACING_BALL]
        _STATE_MAP = {NOT_FACING_BALL: self.do_nothing()}
        super(PassBall, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
