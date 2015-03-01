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
                   GRABBING_BALL, TESTING_GRAB, POSSESSION]
        _STATE_MAP = {NOT_FACING_BALL: self.face_ball,
                      FACING_BALL: self.open_grabber,
                      GRABBER_OPEN: self.move_to_ball,
                      GRABBING_BALL: self.grab_ball,
                      TESTING_GRAB: self.test_grab,
                      POSSESSION: self.do_nothing}
        super(GetBall, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.ball = self.world.ball
        self.grab_successful = False
        self.grab_testing = False

    def transition(self):
        print self.robot_mdl.can_catch_ball(self.ball)
        print self.state
        if self.grab_successful:
            self.state = POSSESSION
        elif self.grab_testing:
            self.state = TESTING_GRAB
        elif not self.facing_ball():
            self.state = NOT_FACING_BALL
        elif not self.robot_ctl.grabber_open and not self.robot_mdl.can_catch_ball(self.ball):
            self.state = FACING_BALL
        elif not self.robot_mdl.can_catch_ball(self.world.ball):
            self.state = GRABBER_OPEN
        else:
            self.state = GRABBING_BALL

    def facing_ball(self):
        ball = self.world.ball
        angle_to_ball = self.robot_mdl.get_rotation_to_point(ball.x, ball.y)
        return -ROTATE_MARGIN < angle_to_ball < ROTATE_MARGIN

    def ball_in_danger_zone(self):
        ball = self.world.ball
        ball_dist = self.robot_mdl.get_displacement_to_point(ball.x, ball.y)
        return ball_dist < 45  # MAGIC NUMBER WOOOOOOO

    def face_ball(self):
        """
        Command the robot to turn to face the ball.
        """
        if self.robot_ctl.grabber_open and not self.robot_ctl.is_grabbing and\
                self.ball_in_danger_zone() and not self.robot_mdl.can_catch_ball(self.ball):
            self.robot_ctl.close_grabber()
        elif not self.robot_ctl.is_moving:
            angle_to_ball = self.robot_mdl.get_rotation_to_point(self.ball.x,
                                                                 self.ball.y)
            self.robot_ctl.turn(angle_to_ball, 80)
        else:
            self.robot_ctl.update_state()

    def move_to_ball(self):
        """
        Command the robot to move to the ball.
        """
        if not self.robot_ctl.is_moving:
            dist = self.robot_mdl.get_displacement_to_point(self.ball.x,
                                                            self.ball.y)
            self.robot_ctl.drive(px_to_cm(dist), px_to_cm(dist), 90, 90)
        else:
            self.robot_ctl.update_state()

    def open_grabber(self):
        if not self.robot_ctl.grabber_open and not self.robot_ctl.is_grabbing and\
                not self.robot_mdl.can_catch_ball(self.ball):
            self.robot_ctl.open_grabber()
        else:
            self.robot_ctl.update_state()

    def grab_ball(self):
        """
        Command the robot to grab the ball. Test the grab
        """
        if not self.robot_ctl.is_grabbing:
            if self.robot_ctl.grabber_open:
                self.robot_ctl.close_grabber()
            else:
                self.grab_testing = True
                self.robot_ctl.turn(math.pi, 70)
        else:
            self.robot_ctl.update_state()

    def test_grab(self):
        """
        Check the grab test initiated by the grab_ball method.
        """
        if not self.robot_ctl.is_moving:  # Done spinning
            if self.robot_mdl.can_catch_ball(self.ball):  # Still in grabber
                self.grab_successful = True
                self.grab_testing = False
            else:
                self.grab_testing = False
        else:
            self.robot_ctl.update_state()


class PassBall(Strategy):
    """
    Have the robot find a path and pass to the defending robot.
    Intended use is when the ball is in our possession.
    """
    def __init__(self, world, robot_ctl):
        _STATES = [FIND_PATH, HAS_LOS, FACING_DEFENDER, GRABBER_OPEN, KICKED]
        _STATE_MAP = {FIND_PATH: self.move_to_los,
                      HAS_LOS: self.face_defender,
                      FACING_DEFENDER: self.open_grabber,
                      GRABBER_OPEN: self.kick,
                      KICKED: self.do_nothing}

        super(PassBall, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.target = self.world.our_defender
        self.their_attacker = self.world.their_attacker
        self.has_kicked = False

    def transition(self):
        pass_path = self.robot_mdl.get_pass_path(self.target)
        angle_to_def = self.robot_mdl.get_rotation_to_point(self.target.x, self.target.y)
        spot = self.calc_freespot()
        if self.has_kicked:
            self.state = GRABBER_OPEN
        elif pass_path.isInside(self.their_attacker.x, self.their_attacker.y):
            self.state = FIND_PATH
        elif not -ROTATE_MARGIN < angle_to_def < ROTATE_MARGIN:
            self.state = HAS_LOS
        elif not self.robot_ctl.grabber_open:
            self.state = FACING_DEFENDER
        else:
            self.state = GRABBER_OPEN

    def move_to_los(self):
        """
        Command the robot to move to the ball.
        """
        spot = self.calc_freespot()
        angle = self.robot_mdl.get_rotation_to_point(spot[0], spot[1])
        dist = self.robot_mdl.get_displacement_to_point(spot[0], spot[1])

        if not self.robot_ctl.is_moving:
            if not -ROTATE_MARGIN < angle < ROTATE_MARGIN:
                self.robot_ctl.turn(angle, 80)
            elif dist > 10:
                self.robot_ctl.drive(dist, dist, 90, 90)
        else:
            self.robot_ctl.update_state()

    def face_defender(self):
        """
        Command the robot to turn to face our defender.
        """
        if not self.robot_ctl.is_moving:
            angle_to_def = self.robot_mdl.get_rotation_to_point(self.target.x,
                                                                self.target.y)
            self.robot_ctl.turn(angle_to_def, 80)
        else:
            self.robot_ctl.update_state()

    def kick(self):
        """
        Give the kick command
        """
        self.robot_ctl.kick()
        self.has_kicked = True

    def calc_freespot(self):
        (our_center_x, our_center_y) = self.world.pitch.zones[self.robot_mdl.zone].center()
        (their_center_x, their_center_y) = self.world.pitch.zones[self.world.their_attacker.zone].center()

        if self.world.their_attacker.y > their_center_y:
            freespot_y = (3.0/10) * self.world.pitch.height
        else:
            freespot_y = (7.0/10) * self.world.pitch.height

        freespot_x = int(our_center_x)

        return freespot_x, freespot_y

    def open_grabber(self):
        if not self.robot_ctl.grabber_open and not self.robot_ctl.is_grabbing:
            self.robot_ctl.open_grabber()
        else:
            self.robot_ctl.update_state()


class ShootGoal(Strategy):
    """
    Strategy that makes the robot face the goal and kick given it has a clear 
    line of sight on goal
    """

    def __init__(self, world, robot_ctl):
        _STATES = [FIND_PATH, HAS_LOS, FACING_GOAL, GRABBER_OPEN, KICKED]
        _STATE_MAP = {FIND_PATH: self.move_to_los,
                      HAS_LOS: self.face_goal,
                      FACING_GOAL: self.open_grabber,
                      GRABBER_OPEN: self.kick,
                      KICKED: self.do_nothing}

        super(ShootGoal, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.target = self.world.their_goal
        self.their_defender = self.world.their_defender
        self.has_kicked = False

    def transition(self):
        shooting_path = self.robot_mdl.get_pass_path(self.target) #Using pass path as it achieves the same
        angle_to_goal = self.robot_mdl.get_rotation_to_point(self.target.x, self.target.y)
        spot = self.calc_freespot()
        if self.has_kicked:
            self.state = GRABBER_OPEN # Evil infinite loop to make sure it gets rid of the ball. TODO: Fix
        elif shooting_path.isInside(self.their_defender.x, self.their_defender.y):
            self.state = FIND_PATH
        elif not -ROTATE_MARGIN < angle_to_goal < ROTATE_MARGIN:
            self.state = HAS_LOS
        elif not self.robot_ctl.grabber_open:
            self.state = FACING_GOAL
        else:
            self.state = GRABBER_OPEN

    def move_to_los(self):
        """
        Command the robot to move to a better location.
        """
        spot = self.calc_freespot()
        angle = self.robot_mdl.get_rotation_to_point(spot[0], spot[1])
        dist = self.robot_mdl.get_displacement_to_point(spot[0], spot[1])

        if not self.robot_ctl.is_moving:
            if not -ROTATE_MARGIN < angle < ROTATE_MARGIN:
                self.robot_ctl.turn(angle, 80)
            elif dist > 10:
                self.robot_ctl.drive(dist, dist, 90, 90)
        else:
            self.robot_ctl.update_state()

    def face_goal(self):
        """
        Command the robot to turn to face their goal.
        """
        if not self.robot_ctl.is_moving:
            angle_to_goal = self.robot_mdl.get_rotation_to_point(self.target.x,
                                                                self.target.y)
            self.robot_ctl.turn(angle_to_goal, 80)
        else:
            self.robot_ctl.update_state()

    def kick(self):
        """
        Give the kick command
        """
        self.robot_ctl.kick()
        self.has_kicked = True

    def calc_freespot(self):
        (our_center_x, our_center_y) = self.world.pitch.zones[self.robot_mdl.zone].center()
        (their_center_x, their_center_y) = self.world.pitch.zones[self.world.their_defender.zone].center()

        if self.world.their_defender.y > their_center_y:
            freespot_y = (3.0/10) * self.world.pitch.height
        else:
            freespot_y = (7.0/10) * self.world.pitch.height

        freespot_x = int(our_center_x)

        return freespot_x, freespot_y

    def open_grabber(self):
        if not self.robot_ctl.grabber_open and not self.robot_ctl.is_grabbing:
            self.robot_ctl.open_grabber()
        else:
            self.robot_ctl.update_state()