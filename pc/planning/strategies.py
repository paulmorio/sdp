from utilities import *


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
        self.dest = None  # For shoot and pass strategies, reset on transition

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

    def reset(self):
        """Reset the Strategy object to its initial state."""
        self.state = self.states[0]
        self.dest = None

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
        _STATES = [TURNING_TO_BALL, OPENING_GRABBER,
                   MOVING_TO_BALL, GRABBING_BALL, POSSESSION]
        _STATE_MAP = {TURNING_TO_BALL: self.face_ball,
                      OPENING_GRABBER: self.open_grabber,
                      MOVING_TO_BALL: self.move_to_ball,
                      GRABBING_BALL: self.close_grabber}
        super(GetBall, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.ball = self.world.ball

    def face_ball(self):
        if not self.robot_ctl.is_moving:
            if self.world.can_catch_ball(self.robot_mdl) \
                    and self.robot_ctl.grabber_open:
                self.state = GRABBING_BALL
            elif self.robot_mdl.is_facing_point(self.ball.x, self.ball.y):
                self.state = OPENING_GRABBER
            else:
                angle = self.robot_mdl.get_rotation_to_point(self.ball.x,
                                                             self.ball.y)
                self.robot_ctl.turn(angle)

    def open_grabber(self):
        if not self.robot_ctl.is_grabbing:
            if self.robot_ctl.grabber_open:
                self.state = MOVING_TO_BALL
            elif self.world.ball_too_close(self.robot_mdl):
                self.robot_ctl.drive(-1, -1)
            else:
                self.robot_ctl.open_grabber()

    def move_to_ball(self):
        if not self.robot_ctl.is_moving:
            if self.world.can_catch_ball(self.robot_mdl):
                self.state = GRABBING_BALL
            elif not self.robot_mdl.is_facing_point(self.ball.x, self.ball.y):
                self.state = TURNING_TO_BALL
            else:
                dist = self.robot_mdl.get_displacement_to_point(self.ball.x,
                                                                self.ball.y)
                self.robot_ctl.drive(dist*0.1, dist*0.1)

    def close_grabber(self):
        if not self.robot_ctl.is_grabbing:
            if self.robot_ctl.grabber_open:
                self.robot_ctl.close_grabber()
            elif not self.world.can_catch_ball(self.robot_mdl):
                self.state = TURNING_TO_BALL


class FaceBall(Strategy):
    """
    Ball is not in our margin - face it with the grabber open, ready to receive
    a pass.
    """
    def __init__(self, world, robot_ctl):
        _STATES = [INIT, FOLLOWING_BALL]
        _STATE_MAP = {INIT: self.open_grabber,
                      FOLLOWING_BALL: self.follow_ball}
        super(FaceBall, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)

    def open_grabber(self):
        if not self.robot_ctl.is_grabbing:
            if self.robot_ctl.grabber_open:
                self.state = FOLLOWING_BALL
            else:
                self.robot_ctl.open_grabber()

    def follow_ball(self):
        if not self.robot_mdl.is_facing_point(self.ball.x, self.ball.y) \
                and not self.robot_ctl.is_moving:
            angle = self.robot_mdl.get_rotation_to_point(self.ball.x,
                                                         self.ball.y)
            self.robot_ctl.turn(angle)


class PassBall(Strategy):
    """
    Have the robot find a path and pass to the defending robot.
    Intended use is when the ball is in our possession.
    """
    def __init__(self, world, robot_ctl):
        _STATES = [INIT, FINDING_PATH, MOVING_TO_DEST,
                   TURNING_TO_DEFENDER, OPENING_GRABBER, KICKING,
                   DONE]
        _STATE_MAP = {INIT: self.close_grabber,
                      FINDING_PATH: self.find_path,
                      MOVING_TO_DEST: self.move_to_dest,
                      TURNING_TO_DEFENDER: self.turn_to_def,
                      OPENING_GRABBER: self.open_grabber,
                      KICKING: self.kick,
                      DONE: self.do_nothing}
        super(PassBall, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.target = self.world.our_defender
        self.their_attacker = self.world.their_attacker

    def find_path(self):
        path = self.robot_mdl.get_pass_path(self.target)
        if path.overlaps(self.their_attacker.get_polygon()):  # TODO SLOW
            self.dest = self.world.find_pass_spot_ms3(self.robot_mdl)
            self.state = MOVING_TO_DEST
        else:
            self.state = TURNING_TO_DEFENDER

    def move_to_dest(self):
        if not self.robot_ctl.is_moving:
            if self.robot_mdl.is_at_point(self.dest[0], self.dest[1]):
                self.state = TURNING_TO_DEFENDER
            elif self.robot_mdl.is_facing_point(self.dest[0], self.dest[1]):
                dist = self.robot_mdl.get_displacement_to_point(self.dest[0],
                                                                self.dest[1])
                self.robot_ctl.drive(dist, dist)
            else:
                angle = self.robot_mdl.get_rotation_to_point(self.dest[0],
                                                             self.dest[1])
                self.robot_ctl.turn(angle)

    def turn_to_def(self):
        if not self.robot_ctl.is_moving:
            if self.robot_mdl.is_facing_point(self.target.x, self.target.y):
                self.state = OPENING_GRABBER
            else:
                angle = self.robot_mdl.get_rotation_to_point(self.target.x,
                                                             self.target.y)
                self.robot_ctl.turn(angle)

    def open_grabber(self):
        if not self.robot_ctl.is_grabbing:
            if self.robot_ctl.grabber_open:
                self.state = KICKING
            else:
                self.robot_ctl.open_grabber()

    def close_grabber(self):
        if not self.robot_ctl.is_grabbing:
            if not self.robot_ctl.grabber_open:
                self.state = FINDING_PATH
            else:
                self.robot_ctl.close_grabber()

    def kick(self):
        if not self.robot_ctl.ball_grabbed:
            self.state = DONE
        elif not self.robot_ctl.is_kicking:
            self.robot_ctl.kick()


class ShootGoal(Strategy):
    """
    Have the robot find a path and shoot into the goal.
    Intended use is when the ball is in our possession.
    """
    def __init__(self, world, robot_ctl):
        _STATES = [INIT, FINDING_PATH, MOVING_TO_DEST,
                   TURNING_TO_GOAL, OPENING_GRABBER, KICKING, DONE]
        _STATE_MAP = {INIT: self.close_grabber,
                      GOTO_SHOOT_SPOT: self.go_to_shoot_spot,
                      CHOOSING_SHOT_ANGLE: self.turn_to_shoot,

                      KICKING: self.kick,
                      DONE: self.do_nothing}
        super(ShootGoal, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.target = self.world.their_goal
        self.their_defender = self.world.their_defender
        self.shot_target = None

    def close_grabber(self):
        """
        Ensure that the grabber is closed. This is to account for the case
        where the ball magically appears in our grabber slot without us having
        actually grabbed it.
        """
        if not self.robot_ctl.is_grabbing:
            if not self.robot_ctl.grabber_open:
                self.state = GOTO_SHOOT_SPOT
            elif self.robot_ctl.grabber_open:
                self.robot_ctl.close_grabber()

    def go_to_shoot_spot(self):
        """
        Go to the closest shooting spot.
        """
        if self.dest is None:
            self.dest = self.world.get_shoot_spot()

        if not self.robot_ctl.is_moving:
            # At the destination, move on
            if self.robot_mdl.is_at_point(self.dest[0], self.dest[1]):
                self.robot_ctl.stop()
                self.dest = None
                self.state = CHOOSING_SHOT_ANGLE

            # Else, not facing destination
            elif not self.robot_mdl.is_facing_point(self.dest[0], self.dest[1]):
                angle = self.robot_mdl.get_rotation_to_point(self.dest[0],
                                                             self.dest[1])
                self.robot_ctl.turn(angle)

            # Facing the point, move forward
            else:
                dist = self.robot_mdl.get_displacement_to_point(self.dest[0],
                                                                self.dest[1])
                self.robot_ctl.drive(dist, dist)

    def turn_to_shoot(self):
        """
        Turn to appropriate shot angle. This is going to be a bounce shot if
        there is an obstacle between the shooter and goal.
        """
        if self.shot_target is None:
            self.shot_target = self.world.get_shot_target()

        # Turn to shot target
        if not self.robot_mdl.is_facing_point(self.shot_target[0],
                                              self.shot_target[1], 0.01):
            angle = self.robot_mdl.get_rotation_to_point(self.shot_target[0],
                                                         self.shot_target[1])
            self.robot_ctl.turn(angle)

        else:
            self.state = KICKING

    def kick(self):
        """
        Open grabber then kick.
        """
        if not self.robot_ctl.grabber_open:
            if not self.robot_ctl.is_grabbing:
                self.robot_ctl.open_grabber()

        elif not self.robot_ctl.is_kicking:
            self.robot_ctl.kick()

        else:
            self.state = DONE

    def reset(self):
        """
        Override superclass reset to reset shot target
        """
        super(ShootGoal, self).reset()
        self.shot_target = None


class PenaltyKick(Strategy):
    """
    Turn to the enemy goal and kick into it
    Intended use is when the ball is in our possession during penalty mode.
    """
    def __init__(self, world, robot_ctl):
        _STATES = [TURNING_TO_GOAL, OPENING_GRABBER, KICKING, DONE]
        _STATE_MAP = {TURNING_TO_GOAL: self.turn_to_goal,
                      OPENING_GRABBER: self.open_grabber,
                      KICKING: self.kick,
                      DONE: self.do_nothing}
        super(PenaltyKick, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.target = self.world.their_goal
        self.their_defender = self.world.their_defender
        self.dest = None

    def turn_to_goal(self):
        if not self.robot_ctl.is_moving:
            if self.robot_mdl.is_facing_point(self.target.x, self.target.y):
                self.state = OPENING_GRABBER
            else:
                angle = self.robot_mdl.get_rotation_to_point(self.target.x,
                                                             self.target.y)
                self.robot_ctl.turn(angle)

    def open_grabber(self):
        if not self.robot_ctl.is_grabbing:
            if self.robot_ctl.grabber_open:
                self.state = KICKING
            else:
                self.robot_ctl.open_grabber()

    def close_grabber(self):
        if not self.robot_ctl.is_grabbing:
            if not self.robot_ctl.grabber_open:
                self.state = FINDING_PATH
            elif self.robot_ctl.grabber_open:
                self.robot_ctl.close_grabber()

    def kick(self):
        if not self.robot_ctl.ball_grabbed:
            self.state = DONE
        elif not self.robot_ctl.is_kicking:
            self.robot_ctl.kick()