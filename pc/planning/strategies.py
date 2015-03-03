from utilities import *
import math
from Polygon.cPolygon import Polygon


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

    def facing_point(self, x, y):
        angle = self.robot_mdl.get_rotation_to_point(x, y)
        return -ROTATE_MARGIN < angle < ROTATE_MARGIN

    def calc_freespot(self):
        our_center_x, our_center_y = \
            self.world.pitch.zones[self.robot_mdl.zone].center()
        their_center_x, their_center_y = \
            self.world.pitch.zones[self.world.their_attacker.zone].center()

        if self.world.their_attacker.y > their_center_y:
            freespot_y = (2.0/10) * self.world.pitch.height
        else:
            freespot_y = (8.0/10) * self.world.pitch.height

        # TODO add an offset to make it move to the edge of the margin
        freespot_x = int(our_center_x)

        return freespot_x, freespot_y


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
        _STATES = [TURNING_TO_BALL, OPENING_GRABBER, MOVING_TO_BALL,
                   GRABBING_BALL, POSSESSION]
        _STATE_MAP = {TURNING_TO_BALL: self.face_ball,
                      OPENING_GRABBER: self.open_grabber,
                      MOVING_TO_BALL: self.move_to_ball,
                      GRABBING_BALL: self.grab_ball,
                      POSSESSION: self.do_nothing}
        super(GetBall, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.ball = self.world.ball

    def transition(self):
        if self.robot_ctl.ball_grabbed:  # Have ball, final state
            self.state = POSSESSION
        elif not self.facing_point(self.ball.x, self.ball.y): # Not facing ball
            self.state = TURNING_TO_BALL
        elif not self.robot_ctl.grabber_open:  # Facing ball but grabber is not open
            self.state = OPENING_GRABBER
        elif not self.robot_mdl.can_catch_ball(self.world.ball): # Not close enough
            self.state = MOVING_TO_BALL
        else:
            self.state = GRABBING_BALL

    def face_ball(self):
        """
        Command the robot to turn to face the ball.
        """
        # If the grabber is open, the ball is too close to turn, close the grabber.
        if self.robot_ctl.grabber_open and not self.robot_ctl.is_grabbing \
                and self.ball_in_danger_zone():
            self.robot_ctl.close_grabber()

        elif not self.robot_ctl.is_moving:
            angle_to_ball = self.robot_mdl.get_rotation_to_point(self.ball.x,
                                                                 self.ball.y)
            self.robot_ctl.turn(angle_to_ball)
        else:
            self.robot_ctl.update_state()

    def move_to_ball(self):
        """
        Command the robot to move to the ball.
        """
        if not self.robot_ctl.is_moving:
            dist = self.robot_mdl.get_displacement_to_point(self.world.ball.x,
                                                            self.world.ball.y)
            self.robot_ctl.drive(dist*0.5, dist*0.5)
        else:
            self.robot_ctl.update_state()

    def grab_ball(self):
        """
        Command the robot to grab the ball.
        """
        if not self.robot_ctl.is_grabbing and self.robot_ctl.grabber_open:
            self.robot_ctl.close_grabber()
        else:
            self.robot_ctl.update_state()

    def ball_in_danger_zone(self):
        """
        True if the ball is within DANGER_ZONE_CM of the robot.
        """
        ball = self.world.ball
        ball_dist = self.robot_mdl.get_displacement_to_point(ball.x, ball.y)
        return ball_dist < DANGER_ZONE_CM

    def open_grabber(self):
        if not self.robot_ctl.grabber_open \
                and not self.robot_ctl.is_grabbing \
                and not self.robot_mdl.can_catch_ball(self.ball):
            if self.ball_in_danger_zone():  # TODO SHITE FIX
                self.robot_ctl.drive(-3, -3)
            else:
                self.robot_ctl.open_grabber()
        else:
            self.robot_ctl.update_state()


class FaceBall(Strategy):
    """
    Ball is not in our margin - face it with the grabber open, ready to receive
    a pass.
    """
    def __init__(self, world, robot_ctl):
        _STATES = [GRABBER_CLOSED, FINDING_BALL, FACING_BALL]
        _STATE_MAP = {GRABBER_CLOSED: self.open_grabber,
                      FINDING_BALL: self.follow_ball,
                      FACING_BALL: self.do_nothing}
        super(FaceBall, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)

    def transition(self):
        if not self.robot_ctl.grabber_open:
            self.state = GRABBER_CLOSED
        elif not self.facing_point(self.world.ball.x, self.world.ball.y):
            self.state = FINDING_BALL
        else:
            self.state = FACING_BALL

    def follow_ball(self):
        if not self.robot_ctl.is_moving:
            angle_to_ball = self.robot_mdl.get_rotation_to_point(self.ball.x,
                                                                 self.ball.y)
            self.robot_ctl.turn(angle_to_ball)
        else:
            self.robot_ctl.update_state()

    def open_grabber(self):
        if not self.robot_ctl.is_grabbing:
            self.robot_ctl.open_grabber()
        else:
            self.robot_ctl.update_state()


class PassBall(Strategy):
    """
    Have the robot find a path and pass to the defending robot.
    Intended use is when the ball is in our possession.
    """
    def __init__(self, world, robot_ctl):
        _STATES = [FINDING_PATH, TURNING_TO_DEFENDER,
                   OPENING_GRABBER, MOVING_TO_BALL, KICKED]
        _STATE_MAP = {FINDING_PATH: self.move_to_los,
                      TURNING_TO_DEFENDER: self.face_defender,
                      OPENING_GRABBER: self.open_grabber,
                      MOVING_TO_BALL: self.kick,
                      KICKED: self.do_nothing}

        super(PassBall, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.target = self.world.our_defender
        self.their_attacker = self.world.their_attacker
        self.spot = None

    def transition(self):
        pass_path = self.robot_mdl.get_pass_path(self.target)
        angle_to_def = self.robot_mdl.get_rotation_to_point(self.target.x,
                                                            self.target.y)
        # Their attacker is in our pass path, or we already have a destination
        if self.spot is not None or \
                Polygon(self.their_attacker.get_polygon()).overlaps(pass_path):
            self.state = FINDING_PATH
        elif not self.robot_ctl.ball_grabbed:  # Get pulled out of this strat
            self.state = KICKED
        elif not -ROTATE_MARGIN < angle_to_def < ROTATE_MARGIN:
            self.state = TURNING_TO_DEFENDER
        elif self.robot_ctl.grabber_open and not self.robot_ctl.is_grabbing:
            self.state = MOVING_TO_BALL
        else:
            self.state = OPENING_GRABBER

    def move_to_los(self):
        """
        Command the robot to move to the ball.
        """
        if self.robot_ctl.grabber_open and not self.robot_ctl.is_grabbing:
            if self.spot is None:
                self.spot = self.calc_freespot()
            dist, angle = self.robot_mdl.get_direction_to_point(self.spot[0], self.spot[1])

            if not self.robot_ctl.is_moving:
                if not -ROTATE_MARGIN < angle < ROTATE_MARGIN:
                    self.robot_ctl.turn(angle)
                else:
                    self.robot_ctl.drive(dist*0.5, dist*0.5)
            else:
                self.robot_ctl.update_state()
        elif not self.robot_ctl.is_grabbing:
            self.robot_ctl.close_grabber()
        else:
            self.robot_ctl.update_state()

    def face_defender(self):
        """
        Command the robot to turn to face our defender.
        """
        if self.robot_ctl.grabber_open:
            if not self.robot_ctl.is_moving:
                angle_to_def = self.robot_mdl.get_rotation_to_point(self.target.x,
                                                                    self.target.y)
                self.robot_ctl.turn(angle_to_def)
            else:
                self.robot_ctl.update_state()
        elif not self.robot_ctl.is_grabbing:
            self.robot_ctl.close_grabber()
        else:
            self.robot_ctl.update_state()

    def kick(self):
        """
        Give the kick command.
        """
        if not self.robot_ctl.is_kicking and self.robot_ctl.grabber_open \
                and not self.robot_ctl.is_grabbing:
            self.robot_ctl.kick()
        else:
            self.robot_ctl.update_state()

    def open_grabber(self):
        if not self.robot_ctl.grabber_open and not self.robot_ctl.is_grabbing:
            self.robot_ctl.open_grabber()
        else:
            self.robot_ctl.update_state()

    def reset(self):
        self.spot = None
        self.state = self.states[0]


class ShootGoal(Strategy):
    """
    Strategy that makes the robot face the goal and kick given it has a clear 
    line of sight on goal
    """

    def __init__(self, world, robot_ctl):
        _STATES = [FINDING_PATH, TURNING_TO_DEFENDER,
                   FACING_GOAL, MOVING_TO_BALL, KICKED]
        _STATE_MAP = {FINDING_PATH: self.move_to_los,
                      TURNING_TO_DEFENDER: self.face_goal,
                      FACING_GOAL: self.open_grabber,
                      MOVING_TO_BALL: self.kick,
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
            self.state = MOVING_TO_BALL # Evil infinite loop to make sure it gets rid of the ball. TODO: Fix
        elif shooting_path.isInside(self.their_defender.x, self.their_defender.y):
            self.state = FINDING_PATH
        elif not -ROTATE_MARGIN < angle_to_goal < ROTATE_MARGIN:
            self.state = TURNING_TO_DEFENDER
        elif not self.robot_ctl.grabber_open:
            self.state = FACING_GOAL
        else:
            self.state = MOVING_TO_BALL

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

    def open_grabber(self):
        if not self.robot_ctl.grabber_open and not self.robot_ctl.is_grabbing:
            self.robot_ctl.open_grabber()
        else:
            self.robot_ctl.update_state()