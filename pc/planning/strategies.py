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
        if not self.robot_ctl.is_moving and not self.robot_mdl.is_turning():
            if self.world.can_catch_ball(self.robot_mdl) \
                    and self.robot_ctl.grabber_open:
                self.state = GRABBING_BALL
            elif self.robot_mdl.is_facing_point(self.ball.x, self.ball.y):
                self.state = OPENING_GRABBER
            else:
                angle = self.robot_mdl.get_rotation_to_point(self.ball.x,
                                                             self.ball.y)
                self.robot_ctl.turn(angle*0.3)

    def open_grabber(self):
        if not self.robot_ctl.is_grabbing:
            if self.robot_ctl.grabber_open:
                self.state = MOVING_TO_BALL
            elif self.world.ball_too_close(self.robot_mdl):  # SAFE SPACE POLICY
                self.robot_ctl.drive(-1, -1)               # TODO MAGIC
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
                self.robot_ctl.drive(dist, dist)

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
            self.robot_ctl.turn(angle*0.3)


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

    def find_path(self):
        path = self.robot_mdl.get_pass_path(self.target)
        if path.overlaps(self.their_attacker.get_polygon()):
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
                self.robot_ctl.turn(angle*0.3)

    def turn_to_def(self):
        if not self.robot_ctl.is_moving:
            if self.robot_mdl.is_facing_point(self.target.x, self.target.y):
                self.state = OPENING_GRABBER
            else:
                angle = self.robot_mdl.get_rotation_to_point(self.target.x,
                                                             self.target.y)
                self.robot_ctl.turn(angle*0.3)

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

    def reset(self):
        super(PassBall, self).reset()
        self.dest = None


class ShootGoal(Strategy):
    """
    Have the robot find a path and shoot into the goal.
    Intended use is when the ball is in our possession.
    """
    def __init__(self, world, robot_ctl):
        _STATES = [INIT, GOTO_SHOOT_SPOT, CHOOSING_SHOT_ANGLE, KICKING, DONE]
        _STATE_MAP = {INIT: self.close_grabber,
                      GOTO_SHOOT_SPOT: self.go_to_shoot_spot,
                      CHOOSING_SHOT_ANGLE: self.turn_to_shoot,
                      KICKING: self.kick,
                      DONE: self.do_nothing}

        super(ShootGoal, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.target = self.world.their_goal
        self.their_defender = self.world.their_defender
        self.shot_target = None
        self.dest = None

    def close_grabber(self):
        """
        Ensure that the grabber is closed. This is to account for the case
        where the ball magically appears in our grabber slot without us having
        actually grabbed it.
        """
        if not self.robot_ctl.is_grabbing:
            if not self.robot_ctl.grabber_open:
                self.state = GOTO_SHOOT_SPOT
            else:
                self.robot_ctl.close_grabber()

    def go_to_shoot_spot(self):
        """
        Go to the closest shooting spot.
        """
        if self.dest is None:
            self.dest = self.world.get_shot_spot()

        if not self.robot_ctl.is_moving:
            # At the destination, move on
            if self.robot_mdl.is_at_point(self.dest[0], self.dest[1]):
                self.dest = None
                self.state = CHOOSING_SHOT_ANGLE

            # Else, not facing destination
            elif not self.robot_mdl.is_facing_point(self.dest[0], self.dest[1]):
                angle = self.robot_mdl.get_rotation_to_point(self.dest[0],
                                                             self.dest[1])
                print "turning: "+str(angle*0.3)
                self.robot_ctl.turn(angle*0.3) #note: 0.3 = slowing down turn

            # Facing the point, move forward
            else:
                dist = self.robot_mdl.get_displacement_to_point(self.dest[0],
                                                                self.dest[1])
                print "driving: "+str(dist)
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
            self.robot_ctl.turn(angle*0.3)

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


class Defend(Strategy):
    """
    Sit in front of their defender. Very upsetting.

    Intended use is when their defender is contemplating a pass - once the ball
    actually starts moving then the intercept strategy should be selected.
    """
    def __init__(self, world, robot_ctl):
        _STATES = [TURNING_TO_DEST, MOVING_TO_DEST]
        _STATE_MAP = {TURNING_TO_DEST: self.turn_to_dest,
                      MOVING_TO_DEST: self.move_to_dest}
        super(Defend, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.dest = None

    def get_dest(self):
        pass

    def turn_to_dest(self):
        pass

    def move_to_dest(self):
        pass


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
        angle_top = self.robot_mdl.get_rotation_to_angle(math.pi / 2)
        angle_bottom = self.robot_mdl.get_rotation_to_angle(3*math.pi/2)

        self.top_fixated = abs(angle_top) < abs(angle_bottom)
        self.state = TURNING_TO_WALL
        self.turn_to_wall()

    def turn_to_wall(self):
        """
        Make the robot face the fixated wall
        """
        if not self.robot_ctl.is_moving and not self.robot_mdl.is_turning():
            if self.top_fixated:  # Face wall at pi/2
                if self.robot_mdl.is_facing_angle(math.pi/2):
                    self.state = TRACKING_BALL
                else:
                    angle = self.robot_mdl.get_rotation_to_angle(math.pi/2)
                    self.robot_ctl.turn(angle*0.3)  # TODO MAGIC <-- how is this useful?!
            else:
                if self.robot_mdl.is_facing_angle(3*math.pi/2):
                    self.state = TRACKING_BALL
                else:
                    angle = self.robot_mdl.get_rotation_to_angle(3*math.pi/2)
                    self.robot_ctl.turn(angle*0.3)

    def track_ball(self):
        """
        Follow ball's y coordinate.
        """
        if self.robot_mdl.is_square():
            if not self.robot_ctl.is_moving:
                ball_y = self.world.ball.y
                bot_y = self.robot_mdl.y

                if not ball_y - 8 < bot_y < ball_y + 8:
                    displacement = self.world.px_to_cm(ball_y - bot_y)
                    if self.top_fixated:
                        self.robot_ctl.drive(displacement, displacement)
                    else:
                        self.robot_ctl.drive(-displacement, -displacement)
        else:
            self.state = FIXATE

    def reset(self):
        super(Intercept, self).reset()


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
    def __init__(self, world, robot_ctl):
        _STATES = [MOVING_TO_DEST, OPENING_GRABBER, TURNING_TO_BALL]
        _STATE_MAP = {MOVING_TO_DEST: self.move_to_pass_point,
                      OPENING_GRABBER: self.open_grabber,
                      TURNING_TO_WALL: self.face_wall_point}
        super(AwaitPass, self).__init__(world, robot_ctl, _STATES, _STATE_MAP)
        self.dest = None
        self.wall_point = None

    def move_to_pass_point(self):
        if self.dest is None:
            self.dest = self.world.get_pass_receive_spot()

        if not self.robot_ctl.is_moving and not self.robot_mdl.is_turning():
            if self.robot_mdl.is_at_point(self.dest[0], self.dest[1]):
                self.dest = None
                self.state = TURNING_TO_WALL
            if self.robot_mdl.is_facing_point(self.dest[0], self.dest[1]):
                dist = self.robot_mdl.get_displacement_to_point(self.dest[0],
                                                                self.dest[1])
                self.robot_ctl.drive(dist, dist)
            else:
                angle = self.robot_mdl.get_rotation_to_point(self.dest[0],
                                                             self.dest[1])
                self.robot_ctl.turn(angle*0.3)

    def face_wall_point(self):
        if self.wall_point is None:
            pitch_center_y = \
                self.world.pitch.zones[self.robot_mdl.zone].center()[1]
            x = self.world.pitch.width / 2.0
            if self.robot_mdl.y > pitch_center_y:  # TODO oh oh oh it's magic
                y = self.world.pitch.height - 10
            else:
                y = 10
            self.wall_point = x, y

        if not self.robot_ctl.is_moving and not self.robot_mdl.is_turning():
            if self.robot_mdl.is_facing_point(self.wall_point[0],
                                              self.wall_point[1]):
                self.state = OPENING_GRABBER
                self.wall_point = None
            else:
                angle = self.robot_mdl.get_rotation_to_point(self.wall_point[0],
                                                             self.wall_point[1])
                self.robot_ctl.turn(angle*0.3)

    def open_grabber(self):
        if not self.robot_ctl.grabber_open and not self.robot_ctl.is_grabbing:
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

    def turn_to_goal(self):

        # Decide to aim at the top or bottom wall
        center_y = self.world.their_goal.y

        if self.their_defender.y < center_y:
            aim_top = True
        else:
            aim_top = False

        print "Aim-top: "+str(aim_top)

        # Convert coordinates to wall-bounce coordinates
        #(wall_x, wall_y) = (self.target.x, self.target.y)
        (wall_x, wall_y) = self.robot_mdl.get_point_via_wall(self.target.x, self.target.y, aim_top)

        # Rotate robot to point if required, otherwise new state: open grabber
        if not self.robot_ctl.is_moving and not self.robot_mdl.is_turning():
            if self.robot_mdl.is_facing_point(wall_x, wall_y):
                self.state = OPENING_GRABBER
            else:
                angle = self.robot_mdl.get_rotation_to_point(wall_x,
                                                             wall_y)
                print "giving task to turn: "+str(angle*0.3)+" deg"
                self.robot_ctl.turn(angle*0.3)

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