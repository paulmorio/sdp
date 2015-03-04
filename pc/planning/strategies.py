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
        if self.world.can_catch_ball(self.robot_mdl) \
                and self.robot_ctl.grabber_open:
            self.state = GRABBING_BALL
        elif self.robot_mdl.is_facing_point(self.ball.x, self.ball.y):
            self.state = OPENING_GRABBER
        elif not self.robot_ctl.is_moving:
            angle = self.robot_mdl.get_rotation_to_point(self.ball.x,
                                                         self.ball.y)
            self.robot_ctl.turn(angle)
        else:
            self.robot_ctl.update_state()

    def open_grabber(self):

        if self.robot_ctl.grabber_open:
            self.state = MOVING_TO_BALL
        elif self.world.ball_too_close(self.robot_mdl):
            self.robot_ctl.drive(-1, -1)
        elif not self.robot_ctl.is_grabbing:
            self.robot_ctl.open_grabber()
        else:
            self.robot_ctl.update_state()

    def move_to_ball(self):
        if self.world.can_catch_ball(self.robot_mdl):
            self.state = GRABBING_BALL
        elif not self.robot_mdl.is_facing_point(self.ball.x, self.ball.y):
            self.state = TURNING_TO_BALL
        elif not self.robot_ctl.is_moving:
            dist = self.robot_mdl.get_displacement_to_point(self.ball.x,
                                                            self.ball.y)
            self.robot_ctl.drive(dist*0.1, dist*0.1)
        else:
            self.robot_ctl.update_state()

    def close_grabber(self):
        if self.robot_ctl.grabber_open and not self.robot_ctl.is_grabbing:
            self.robot_ctl.close_grabber()
        elif not self.world.can_catch_ball(self.robot_mdl):
            self.state = TURNING_TO_BALL
        else:
            self.robot_ctl.update_state()


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
        if self.robot_ctl.grabber_open:
            self.state = FOLLOWING_BALL
        elif not self.robot_ctl.is_grabbing:
            self.robot_ctl.open_grabber()
        else:
            self.robot_ctl.update_state()

    def follow_ball(self):
        if not self.robot_mdl.is_facing_point(self.ball.x, self.ball.y) \
                and not self.robot_ctl.is_moving:
            angle = self.robot_mdl.get_rotation_to_point(self.ball.x,
                                                         self.ball.y)
            self.robot_ctl.turn(angle)
        else:
            self.robot_ctl.update_state()


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
        self.dest = None

    def close_grabber(self):
        if not self.robot_ctl.grabber_open:
            self.state = FINDING_PATH
        elif self.robot_ctl.grabber_open and not self.robot_ctl.is_grabbing:
            self.robot_ctl.close_grabber()
        else:
            self.robot_ctl.update_state()

    def find_path(self):
        path = self.robot_mdl.get_pass_path(self.target)
        if path.isInside(self.their_attacker.x, self.their_attacker.y):
            self.dest = self.world.find_line_of_sight(self.robot_mdl)
            self.state = MOVING_TO_DEST
        else:
            self.state = TURNING_TO_DEFENDER

    def move_to_dest(self):
        if self.robot_mdl.is_at_point(self.dest[0], self.dest[1]):
            self.state = TURNING_TO_DEFENDER
        elif self.robot_mdl.is_facing_point(self.dest[0], self.dest[1]):
            dist = self.robot_mdl.get_displacement_to_point(self.dest[0],
                                                            self.dest[1])
            if not self.robot_ctl.is_moving:
                self.robot_ctl.drive(dist, dist)
            else:
                self.robot_ctl.update_state()
        else:
            angle = self.robot_mdl.get_rotation_to_point(self.dest[0],
                                                         self.dest[1])
            if not self.robot_ctl.is_moving:
                self.robot_ctl.turn(angle)
            else:
                self.robot_ctl.update_state()

    def turn_to_def(self):
        if self.robot_mdl.is_facing_point(self.target.x, self.target.y):
            self.state = OPENING_GRABBER
        else:
            angle = self.robot_mdl.get_displacement_to_point(self.target.x,
                                                             self.target.y)
            if not self.robot_ctl.is_moving:
                self.robot_ctl.turn(angle)
            else:
                self.robot_ctl.update_state()

    def open_grabber(self):
        if self.robot_ctl.grabber_open:
            self.state = KICKING
        elif not self.robot_ctl.is_grabbing:
            self.robot_ctl.open_grabber()
        else:
            self.robot_ctl.update_state()

    def kick(self):
        if not self.robot_ctl.ball_grabbed:
            self.state = DONE
        elif not self.robot_ctl.is_kicking:
            self.robot_ctl.kick()
        else:
            self.robot_ctl.update_state()


# class ShootGoal(Strategy):
#     """
#     Strategy that makes the robot face the goal and kick given it has a clear
#     line of sight on goal.
#     NYI
#     """
#
#     def __init__(self, world, robot_ctl):
#         _STATES = [FINDING_PATH, TURNING_TO_GOAL,
#                    KICKING, MOVING_TO_BALL, KICKED]
#         _STATE_MAP = {FINDING_PATH: self.move_to_los,
#                       TURNING_TO_GOAL: self.face_goal,
#                       KICKING: self.open_grabber,
#                       MOVING_TO_BALL: self.kick,
#                       KICKED: self.do_nothing}
#
#         super(ShootGoal, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
#         self.target = self.world.their_goal
#         self.their_defender = self.world.their_defender
#         self.spot = None
#
#     def transition(self):
#         pass_path = self.robot_mdl.get_pass_path(self.target)
#
#         if self.spot is not None or \
#                 self.their_defender.get_polygon().overlaps(pass_path):
#             self.state = FINDING_PATH
#         elif not self.robot_ctl.ball_grabbed:  # Get pulled out of this strat
#             self.state = KICKED
#         elif not self.robot_mdl.is_facing_point(self.target.x, self.target.y):
#             self.state = TURNING_TO_GOAL
#         elif self.robot_ctl.grabber_open and not self.robot_ctl.is_grabbing:
#             self.state = MOVING_TO_BALL
#         else:
#             self.state = KICKING
#
#     def move_to_los(self):
#         """
#         Command the robot to move to the ball.
#         """
#         if self.robot_ctl.grabber_open and not self.robot_ctl.is_grabbing:
#             if self.spot is None:
#                 self.spot = self.world.find_line_of_sight(self.robot_mdl)
#             dist, angle = self.robot_mdl.get_direction_to_point(self.spot[0],
#                                                                 self.spot[1])
#
#             if not self.robot_ctl.is_moving:
#                 if not self.robot_mdl.is_facing_point(self.target.x, self.target.y):
#                     self.robot_ctl.turn(angle)
#                 else:
#                     self.robot_ctl.drive(dist*0.5, dist*0.5)
#             else:
#                 self.robot_ctl.update_state()
#         elif not self.robot_ctl.is_grabbing:
#             self.robot_ctl.close_grabber()
#         else:
#             self.robot_ctl.update_state()
#
#     def face_goal(self):
#         """
#         Command the robot to turn to face their goal.
#         """
#         if self.robot_ctl.grabber_open:
#             if not self.robot_ctl.is_moving:
#                 angle_to_goal = self.robot_mdl.get_rotation_to_point(self.target.x,
#                                                                     self.target.y)
#                 self.robot_ctl.turn(angle_to_goal)
#             else:
#                 self.robot_ctl.update_state()
#         elif not self.robot_ctl.is_grabbing:
#             self.robot_ctl.close_grabber()
#         else:
#             self.robot_ctl.update_state()
#
#     def kick(self):
#         """
#         Give the kick command.
#         """
#         if not self.robot_ctl.is_kicking and self.robot_ctl.grabber_open \
#                 and not self.robot_ctl.is_grabbing:
#             self.robot_ctl.kick()
#         else:
#             self.robot_ctl.update_state()
#
#     def open_grabber(self):
#         if not self.robot_ctl.grabber_open and not self.robot_ctl.is_grabbing:
#             self.robot_ctl.open_grabber()
#         else:
#             self.robot_ctl.update_state()
#
#     def reset(self):
#         self.spot = None
#         self.state = self.states[0]
