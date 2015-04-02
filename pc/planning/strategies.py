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
        self.robot_ctl.update_state()
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

    def do_nothing(self):  # Dummy
        pass

    def robot_moving(self):
        """ Check if vision or robot feedback believes the robot is moving"""
        return self.robot_ctl.is_moving or self.robot_mdl.is_moving()


class Idle(Strategy):
    """
    The idle strategy has the robot do nothing.
    Intended use is when the ball is not visible or not reachable by the robot.

    Note that, in the case where vision is a bit dodgy, it's best to simply
    have this do nothing. Otherwise if the ball 'disappears' momentarily
    then the robot may run off somewhere for no clear reason, or whichever
    action is here.
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
                      GRABBING_BALL: self.close_grabber,
                      POSSESSION: self.do_nothing}
        super(GetBall, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.ball = self.world.ball

    def face_ball(self):
        """
        Turn to face the ball then transition to opening_grabber state.
        """
        if not self.robot_moving():
            if self.robot_mdl.is_facing_point(self.ball.x, self.ball.y):
                self.state = OPENING_GRABBER
            else:
                angle = self.robot_mdl.rotation_to_point(self.ball.x,
                                                         self.ball.y)
                self.robot_ctl.turn(angle)

    def open_grabber(self):
        """
        Open the grabber then transition to moving_to_ball state.
        """
        # If the ball is too close for the grabber to be opened then shift back
        if self.world.ball_too_close(self.robot_mdl):
            self.robot_ctl.drive(-2, -2)  # Magic numbers - 2cm works well

        # Send the open command
        else:
            self.robot_ctl.open_grabber()
            # Transition when we see the grabber motor is actually running
            if self.robot_ctl.is_grabbing:
                self.state = MOVING_TO_BALL

    def move_to_ball(self):
        """
        Move to the ball then transition to the closing_grabber state.
        """
        # If we can catch then do so
        if self.world.can_catch_ball(self.robot_mdl):
            self.state = GRABBING_BALL

        elif not self.robot_moving():
            # Are we still facing the ball?
            if not self.robot_mdl.is_facing_point(self.ball.x, self.ball.y):
                self.state = TURNING_TO_BALL

            else:  # Move towards the ball
                dist = self.robot_mdl.displacement_to_point(self.ball.x,
                                                                self.ball.y)
                # Bit of a hack because we have no notion of distance from the
                # grabber area to the ball - the distance is from the
                # center of the plate.
                dist = dist - 10 if dist > 10 else dist * 0.1
                self.robot_ctl.drive(dist, dist)

    def close_grabber(self):
        """
        Close the grabber and transition to the (final) possession state once
        possession is confirmed by robot feedback.
        """
        # If we're not already grabbing then close the grabber until the
        # feedback from the grabber switch reads true - then transition.
        if not self.robot_ctl.is_grabbing:
            self.robot_ctl.close_grabber()
            if self.robot_ctl.ball_grabbed:
                self.state = POSSESSION


class ShootGoal(Strategy):
    """
    Have the robot find a path and shoot into the goal.
    Intended use is when the ball is in our possession.
    """
    def __init__(self, world, robot_ctl):
        _STATES = [INIT, GOTO_SHOOT_SPOT, CHOOSING_SHOT_ANGLE, KICKING]
        _STATE_MAP = {INIT: self.close_grabber,
                      GOTO_SHOOT_SPOT: self.go_to_shoot_spot,
                      CHOOSING_SHOT_ANGLE: self.turn_to_shoot,
                      KICKING: self.kick}

        super(ShootGoal, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.target = self.world.their_goal
        self.their_defender = self.world.their_defender
        self.dest = None  # Point from which we'll shoot

    def close_grabber(self):
        """
        Ensure that the grabber is closed. This is to account for the case
        where the ball magically appears in our grabber slot without us having
        actually grabbed it.

        The aforementioned case occurs because the top-level will push us into
        this strategy when the grabber button is pressed, regardless of what
        was happening before.
        """
        # Yes this will run even if the grabber is closed. It's fine, we have
        # clutch gears.
        if not self.robot_ctl.is_grabbing:
            self.robot_ctl.close_grabber()
        else:
            self.state = GOTO_SHOOT_SPOT

    def go_to_shoot_spot(self):
        """
        Go to the closest shooting spot.
        """
        if self.dest is None:
        # TODO if there is a clear shot from here, take it
            if False:
                self.dest = self.robot_mdl.x, self.robot_mdl.y
        # Choose a spot from which there is a clear shot
            else:
                self.dest = self.world.get_shot_spot()

        if not self.robot_moving():
            # At the destination, move on TODO adjust threshold
            if self.robot_mdl.is_at_point(self.dest[0], self.dest[1]):
                self.dest = None
                self.state = CHOOSING_SHOT_ANGLE

            # Not facing destination - turn
            elif not self.robot_mdl.is_facing_point(self.dest[0], self.dest[1]):
                angle = self.robot_mdl.rotation_to_point(self.dest[0],
                                                         self.dest[1])
                self.robot_ctl.turn(angle)

            # Move to destination
            else:
                dist = self.robot_mdl.displacement_to_point(self.dest[0],
                                                            self.dest[1])
                self.robot_ctl.drive(dist, dist)

    def turn_to_shoot(self):
        """
        Turn to appropriate shot angle. This is going to be a bounce shot if
        there is an obstacle between the shooter and goal.
        """
        # Get a clear shot target
        shot_target = self.world.get_shot_target()

        # Turn to shot target if necessary TODO adjust threshold
        if not self.robot_mdl.is_facing_point(shot_target[0], shot_target[1]):
            angle = self.robot_mdl.rotation_to_point(shot_target[0],
                                                     shot_target[1])
            self.robot_ctl.turn(angle)

        # Facing the target - kick!
        else:
            self.state = KICKING

    def kick(self):
        """
        Open grabber then kick.
        """
        # Wait until turning is done from turn_to_shoot state
        if not self.robot_moving():
            # Open grabber if necessary
            if not self.robot_ctl.grabber_open:
                if not self.robot_ctl.is_grabbing:
                    self.robot_ctl.open_grabber()

            else:
                self.robot_ctl.kick()


class Defend(Strategy):
    """
    Sit in front of their defender. Very upsetting.

    Intended use is when their defender is contemplating a pass - once the ball
    actually starts moving then the intercept strategy should be selected.
    """
    # TODO refactor this and intercept - lots of duplicate code
    def __init__(self, world, robot_ctl):
        _STATES = [FIXATE, TURNING_TO_WALL, TRACKING_SHOT_PATH]
        _STATE_MAP = {FIXATE: self.choose_wall,
                      TURNING_TO_WALL: self.turn_to_wall,
                      TRACKING_SHOT_PATH: self.track_shot_path}
        super(Defend, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.top_fixated = None

    def choose_wall(self):
        angle_top = self.robot_mdl.rotation_to_angle(math.pi / 2)
        angle_bottom = self.robot_mdl.rotation_to_angle(3*math.pi/2)
        self.top_fixated = abs(angle_top) < abs(angle_bottom)
        self.state = TURNING_TO_WALL
        self.turn_to_wall()

    def turn_to_wall(self):
        if not self.robot_moving():
            if self.top_fixated:  # Face wall at pi/2
                if self.robot_mdl.is_facing_angle(math.pi/2):
                    self.state = TRACKING_SHOT_PATH
                else:
                    angle = self.robot_mdl.rotation_to_angle(math.pi/2)
                    self.robot_ctl.turn(angle)
            else:
                if self.robot_mdl.is_facing_angle(3*math.pi/2):
                    self.state = TRACKING_SHOT_PATH
                else:
                    angle = self.robot_mdl.rotation_to_angle(3*math.pi/2)
                    self.robot_ctl.turn(angle)

    def track_shot_path(self):
        # find y where shot path intercepts our x
        # Margin 'prevents' us running into the walls
        y_max = self.world.pitch.height * 0.9
        y_min = self.world.pitch.height * 0.1
        their_def = self.world.their_defender

        if self.world.our_side == 'left':
            # Facing top-right - no intercept. Track their y instead.
            if 4 * math.pi / 3 < their_def.angle < math.pi / 2:
                target_y = their_def.y

            # Facing bottom-right - no intercept. Track their y instead.
            elif their_def.angle > 3 * math.pi / 2:
                target_y = their_def.y

            else:  # Get point of intersection TODO refactor
                # Get shot line
                slope = math.tan(their_def.angle)
                offset = their_def.y - slope*their_def.x
                intersection = slope * self.robot_mdl.x + offset

                # Set y within bounds
                if intersection > y_max:
                    target_y = y_max
                elif intersection < y_min:
                    target_y = y_min
                else:
                    target_y = intersection

        else:
            # Their def facing top-left - track y
            if math.pi > their_def.angle > math.pi / 2:
                target_y = their_def.y

            # Their def facing bottom-left - track y
            elif math.pi < their_def.angle < 3 * math.pi / 2:
                target_y = their_def.y

            else:  # Get intersection
                # Get shot line
                slope = math.tan(their_def.angle)
                offset = their_def.y - slope*their_def.x
                intersection = slope * self.robot_mdl.x + offset

                # Set y within bounds
                if intersection > y_max:
                    target_y = y_max
                elif intersection < y_min:
                    target_y = y_min
                else:
                    target_y = intersection

        # move to y
        if not self.robot_moving():
            if not self.robot_mdl.is_square():  # Straighten up
                self.state = TURNING_TO_WALL

            elif not target_y - 8 < self.robot_mdl.y < target_y + 8:
                displacement = self.world.px_to_cm(target_y - self.robot_mdl.y)
                if self.top_fixated:
                    self.robot_ctl.drive(displacement, displacement)
                else:
                    self.robot_ctl.drive(-displacement, -displacement)


class Intercept(Strategy):
    """
    Intercept a moving ball.

    Intended use is where the ball is likely to move across our margin at such
    a speed that it will not stop in the boundary. So likely cases are when
    shots rebound/miss and when their defender attempts a pass.
    """
    def __init__(self, world, robot_ctl):
        _STATES = [FIXATE, TURNING_TO_WALL, TRACKING_BALL]
        _STATE_MAP = {FIXATE: self.choose_wall,
                      TURNING_TO_WALL: self.turn_to_wall,
                      TRACKING_BALL: self.track_ball}
        super(Intercept, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.top_fixated = None

    def choose_wall(self):
        angle_top = self.robot_mdl.rotation_to_angle(math.pi / 2)
        angle_bottom = self.robot_mdl.rotation_to_angle(3*math.pi/2)
        self.top_fixated = abs(angle_top) < abs(angle_bottom)
        self.state = TURNING_TO_WALL
        self.turn_to_wall()

    def turn_to_wall(self):
        """
        Make the robot face the fixated wall
        """
        if not self.robot_moving():
            if self.top_fixated:  # Face wall at pi/2
                if self.robot_mdl.is_facing_angle(math.pi/2):
                    self.state = TRACKING_BALL
                else:
                    angle = self.robot_mdl.rotation_to_angle(math.pi/2)
                    self.robot_ctl.turn(angle)
            else:
                if self.robot_mdl.is_facing_angle(3*math.pi/2):
                    self.state = TRACKING_BALL
                else:
                    angle = self.robot_mdl.rotation_to_angle(3*math.pi/2)
                    self.robot_ctl.turn(angle)

    def track_ball(self):
        """
        Follow ball's y coordinate.
        """
        if self.robot_mdl.is_square():
            if not self.robot_moving():
                ball_y = self.world.ball.y
                bot_y = self.robot_mdl.y

                if not ball_y - 8 < bot_y < ball_y + 8:
                    displacement = self.world.px_to_cm(ball_y - bot_y)
                    if self.top_fixated:
                        self.robot_ctl.drive(displacement, displacement)
                    else:
                        self.robot_ctl.drive(-displacement, -displacement)
        else:
            self.robot_ctl.stop()
            self.state = TURNING_TO_WALL


class AwaitPass(Strategy):
    """
    Go to the pass reception position and face the bounce point. The 'bounce
    point' is the on the wall at the threshold between our margin and the
    opposing attacker's margin. Which wall depends on where the attacker is -
    we choose the wall furthest away from the attacker.

    Intended use is where our defending has the ball and is setting up a pass.
    Note that we must stick in this mode and NOT switch to, i.e., intercept
    when the ball crosses into a different zone - this will cause some funky
    bugs and as such it requires a lot of testing (at the planner level that is)
    """
    # TODO revamp for new team 8 passing strategy
    def __init__(self, world, robot_ctl):
        _STATES = [MOVING_TO_DEST, OPENING_GRABBER, TURNING_TO_WALL]
        _STATE_MAP = {MOVING_TO_DEST: self.move_to_pass_point,
                      OPENING_GRABBER: self.open_grabber,
                      TURNING_TO_WALL: self.face_wall_point}
        super(AwaitPass, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.dest = None
        self.wall_point = None

    def move_to_pass_point(self):
        if self.dest is None:
            self.dest = self.world.get_pass_receive_spot()

        if not self.robot_moving():
            if self.robot_mdl.is_at_point(self.dest[0], self.dest[1]):
                self.dest = None
                self.state = TURNING_TO_WALL
            elif self.robot_mdl.is_facing_point(self.dest[0], self.dest[1]):
                dist = self.robot_mdl.displacement_to_point(self.dest[0],
                                                            self.dest[1])
                self.robot_ctl.drive(dist, dist)
            else:
                angle = self.robot_mdl.rotation_to_point(self.dest[0],
                                                         self.dest[1])
                self.robot_ctl.turn(angle)

    def face_wall_point(self):
        if self.wall_point is None:
            self.wall_point = self.robot_mdl.target_via_wall(
                self.world.our_defender.x, self.world.our_defender.y,
                self.robot_mdl.y > self.world.pitch.height/2.0)

        if not self.robot_moving():
            if self.robot_mdl.is_facing_point(self.wall_point[0],
                                              self.wall_point[1]):
                self.state = OPENING_GRABBER
                self.wall_point = None
            else:
                angle = self.robot_mdl.rotation_to_point(self.wall_point[0],
                                                         self.wall_point[1])
                self.robot_ctl.turn(angle)

    def open_grabber(self):
        if not self.robot_ctl.is_grabbing:
            self.robot_ctl.open_grabber()

    def reset(self):
        super(AwaitPass, self).reset()
        self.dest = None


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
        self.shot_target = None

    def turn_to_goal(self):
        """
        Turn to appropriate shot angle. This is going to be a bounce shot if
        there is an obstacle between the shooter and goal.
        """
        if self.shot_target is None:
            self.shot_target = self.world.get_shot_target()

        # Turn to shot target
        if not self.robot_mdl.is_facing_point(self.shot_target[0],
                                              self.shot_target[1], 0.01):
            angle = self.robot_mdl.rotation_to_point(self.shot_target[0],
                                                         self.shot_target[1])
            self.robot_ctl.turn(angle*0.3)
        else:
            self.state = OPENING_GRABBER

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
            print "ATTEMPT TO KICK"
            self.robot_ctl.kick()