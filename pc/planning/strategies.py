from utilities import *


class Strategy(object):
    """
    A base class on which other strategies should be built. Sets up the
    interface used by the Planner class.
    """
    def __init__(self, world, robot_controller, states, action_map):
        self._STATES = states
        self._STATE_ACTION_MAP = action_map
        assert(self.all_states_mapped())
        self._world = world
        self._robot_controller = robot_controller
        self._state = self._STATES[0]
        self._bot = world.our_attacker

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
        assert (new_state in self._STATES)
        self._state = new_state

    def reset(self):
        """Reset the Strategy object to its initial state."""
        self._state = self._STATES[0]

    def final_state(self):
        """Return True if the current state is final."""
        return self._state == self._STATES[-1]

    def get_action(self):
        """Return the next robot action"""
        action_method = self._STATE_ACTION_MAP[self.state]
        if action_method:
            return action_method()

    def all_states_mapped(self):
        """Return True if all states are mapped to functions"""
        for state in self._STATES:
            if state not in self._STATE_ACTION_MAP:
                return False
        return True

    def do_nothing(self):
        """
        Dummy action for strategies - usually used when in final state.
        :return: None
        """
        print "Doing nothing."
        return None

    def compare_angles(self, angle_1, angle_2):
        """
        Checks if two angles are roughly equal, using the ANGLE_THRESH constant (defined in utilities.py)
        :return: Boolean value, true if they are close, false otherwise
        """
        angle_diff = abs(angle_1 - angle_2)
        if angle_diff < ANGLE_THRESH:
            return True
        return False


class Idle(Strategy):
    """
    The idle strategy is typically the initial strategy and should be returned
    to if the ball is unreachable. This strategy has the robot return to its
    initial position.
    """

    def __init__(self, world, robot_controller):
        self.bot = world.our_attacker

        x, y = world.pitch.zones[self.bot.zone].center()

        self.middle_x = int(x)
        self.middle_y = int(y)

        self.angle = 0

        states = [REORIENT, REPOSITION, IDLE]
        action_map = {
            REORIENT: self.face_pitch_center,
            WAIT_REORIENT: self.do_nothing,
            REPOSITION: self.move_to_origin,
            WAIT_REPOSITION: self.do_nothing,
            IDLE: self.do_nothing()
        }

        super(Idle, self).__init__(world, robot_controller, states, action_map)

    def transition(self):
        print "Idle: " + self.state

        real_angle = self.bot.get_rotation_to_point(self.middle_x, self.middle_y)

        if self.state == REORIENT:
            self.angle = real_angle
            self.state == WAIT_REORIENT

        if self.state == WAIT_REORIENT:
            if abs(self.angle) < ROTATE_MARGIN:
                if self.compare_angles(self.angle, real_angle):
                    self.state = REPOSITION
                else:
                    self.reset()

        elif self.state == REPOSITION:
            displacement = self.bot.get_displacement_to_point(self.middle_x, self.middle_y)
            if displacement < DISPLACEMENT_MARGIN:
                self.state = IDLE
            else:
                self.reset()

    # Actions
    def face_pitch_center(self):
        """
        Face the center of the pitch. Alter the strategy state when necessary.
        :return: An action to be performed by the robot.
        """
        angle = self.bot.get_rotation_to_point(self.middle_x, self.middle_y)
        self._robot_controller.turn(angle)

    def move_to_origin(self):
        """
        Move to the robot's origin. Alter the strategy state when necessary.
        :return: An action to be performed by the robot.
        """
        distance = self.bot.get_displacement_to_point(self.middle_x, self.middle_y)
        self._robot_controller.drive(distance, distance)


class GetBall(Strategy):
    """
    The ball is inside of our attacker's zone, therefore: try to get it
    first open the grabber, aim towards ball, move towards it, and grab it
    """
    def __init__(self, world, robot_controller):
        self.bot = world.our_attacker
        self.ball = world.ball
        self._robot_controller = robot_controller

        self.angle = 0

        states = [OPEN_GRABBER, REORIENT, REPOSITION, CLOSE_GRABBER]
        action_map = {
            OPEN_GRABBER: self._robot_controller.open_grabber,
            WAIT_O_GRAB: self.do_nothing,
            REORIENT: self.aim_towards_ball,
            WAIT_REORIENT: self.do_nothing,
            REPOSITION: self.move_towards_ball,
            WAIT_REPOSITION: self.do_nothing,
            CLOSE_GRABBER: self._robot_controller.close_grabber,
            WAIT_C_GRAB: self.do_nothing
        }

        super(GetBall, self).__init__(world, robot_controller, states, action_map)

    def transition(self):
        print "GetBall: " + self.state

        real_angle = self.bot.get_rotation_to_point(self.ball.x, self.ball.y)

        if self.state == OPEN_GRABBER:
            self.state = WAIT_O_GRAB

        elif self.state == WAIT_O_GRAB:
            if self._robot_controller.open_grabber:
                self.state = REORIENT

        elif self.state == REORIENT:
            self.angle = real_angle
            self.state == WAIT_REORIENT

        elif self.state == WAIT_REORIENT:
            if abs(self.angle) < ROTATE_MARGIN:
                if self.compare_angles(self.angle, real_angle):
                    self.state = REPOSITION
                else:
                    self.reset()

        elif self.state == REPOSITION:
            self.state == WAIT_REPOSITION

        elif self.state == WAIT_REPOSITION:
            if self.bot.can_catch_ball(self.ball):
                self.state = CLOSE_GRABBER
            else:
                self.reset()

        elif self.state == CLOSE_GRABBER:
            if not self.bot.can_catch_ball(self.ball):
                self.reset()
            else:
                self.state == WAIT_C_GRAB

    def aim_towards_ball(self):
        angle = self.bot.get_rotation_to_point(self.ball.x, self.ball.y)
        self._robot_controller.turn(angle)

    def move_towards_ball(self):
        distance = self.bot.get_displacement_to_point(self.ball.x, self.ball.y) - GRAB_AREA_MARGIN
        self._robot_controller.drive(distance, distance)


class CatchBall(Strategy):
    """
    The lazy, no-communication method:
    Sit in the middle of our zone, with the grabber open, facing our teammate
    """
    def __init__(self, world, robot_controller):
        self.bot = world.our_attacker
        self.passer = world.our_defender
        self._robot_controller = robot_controller

        x, y = world.pitch.zones[self.bot.zone].center()

        self.freespot_x = int(x)
        self.freespot_y = int(y)

        self.angle = 0

        states = [OPEN_GRABBER, REORIENT_FREESPOT, REPOSITION, REORIENT_PASSER, IDLE]
        action_map = {
            OPEN_GRABBER: self._robot_controller.open_grabber,
            WAIT_O_GRAB: self.do_nothing,
            REORIENT_FREESPOT: self.aim_towards_freespot,
            WAIT_REORIENT_FREESPOT: self.do_nothing,
            REPOSITION: self.move_towards_freespot,
            WAIT_REPOSITION: self.do_nothing,
            REORIENT_PASSER: self.aim_towards_passer,
            WAIT_REORIENT_PASSER: self.do_nothing,
            IDLE: self.do_nothing
        }

        super(CatchBall, self).__init__(world, robot_controller, states, action_map)

    def transition(self):
        print "CatchBall:" + self.state

        real_angle = self.bot.get_rotation_to_point(self.freespot_x, self.freespot_y)

        # Open the grabber
        if self.state == OPEN_GRABBER:
            self.state == WAIT_O_GRAB

        if self.state == WAIT_O_GRAB:
            if self._robot_controller.grabber_open:
                self.state = REORIENT_FREESPOT

        # Rotate to face the "freespot" (point at center of our zone)
        elif self.state == REORIENT_FREESPOT:
            self.angle = real_angle
            self.state == WAIT_REORIENT_FREESPOT

        elif self.state == WAIT_REORIENT_FREESPOT:
            if abs(self.angle) < ROTATE_MARGIN:
                if self.compare_angles(self.angle, real_angle):
                    self.state = REPOSITION
                else:
                    self.reset()

        # Move to the freespot
        elif self.state == REPOSITION:
            self.state == WAIT_REPOSITION

        elif self.state == WAIT_REPOSITION:
            # if on freespot
            displacement = self.bot.get_displacement_to_point(self.freespot_x, self.freespot_y)
            if displacement < DISPLACEMENT_MARGIN:
                self.state = REORIENT_PASSER
            else:
                self.reset()

        # Rotate to face our passer, and wait
        elif self.state == REORIENT_PASSER:
            self.angle = real_angle
            self.state == WAIT_REORIENT_PASSER

        elif self.staete == WAIT_REORIENT_PASSER:
            if abs(self.angle) < ROTATE_MARGIN:
                if self.compare_angles(self.angle, real_angle):
                    self.state = IDLE
                else:
                    self.reset()

    def aim_towards_freespot(self):
        angle = self.bot.get_rotation_to_point(self.freespot_x, self.freespot_y)
        self._robot_controller.turn(angle)

    def move_towards_freespot(self):
        distance = self.bot.get_displacement_to_point(self.freespot_x, self.freespot_y)
        self._robot_controller(distance, distance)

    def aim_towards_passer(self):
        angle = self.bot.get_rotation_to_point(self.passer.x, self.passer.y)
        self._robot_controller.tunr(angle)


class Confuse(Strategy):
    """
    The ball is in the enemy attacker's zone. Basically there's nothing we can do here.
    """
    def __init__(self, world, robot_controller):
        states = [NONE]
        action_map = {
            NONE: self.do_nothing
        }

        super(Confuse, self).__init__(world, robot_controller, states, action_map)

    def transition(self):
        pass


class Intercept(Strategy):
    """
    The ball is inside the enemy defender's zone
    """
    def __init__(self, world, robot_controller):
        states = [NONE]
        action_map = {
            NONE: self.do_nothing
        }

        super(Intercept, self).__init__(world, robot_controller, states, action_map)

    def transition(self):
        pass


class ShootBall(Strategy):
    """
    Assuming the ball is in possession shoot towards the goal.
    """
    def __init__(self, world, robot_controller):
        self.bot = world.our_attacker
        self._robot_controller = robot_controller

        x, y = world.pitch.zones[self.bot.zone].center()
        self.middle_x = int(x)
        self.middle_y = int(y)

        # Goal
        x, y = world.their_goal.x, world.their_goal.y
        self.goal_x = int(x)
        self.goal_y = int(y)

        self.angle_goal = self.bot.get_rotation_to_point(self.goal_x, self.goal_y)

        states = [REORIENT, REPOSITION, FACE_GOAL, SHOOT]
        action_map = {
            REORIENT: self.face_pitch_center,
            REPOSITION: self.move_to_origin,
            FACE_GOAL: self.face_goal,
            SHOOT: self._robot_controller.kick
        }

        super(ShootBall, self).__init__(world, robot_controller, states, action_map)

    def transition(self):
        print "ShootBall: " + self.state

        # Pitch Center
        angle = self.bot.get_rotation_to_point(self.middle_x, self.middle_y)

        if self.state == REORIENT:
            if self._robot_controller.open_grabber:
                if abs(angle) < ROTATE_MARGIN:
                    self.state = REPOSITION

        elif self.state == REPOSITION:
            displacement = self.bot.get_displacement_to_point(self.middle_x, self.middle_y)
            if displacement < DISPLACEMENT_MARGIN:
                self.state = FACE_GOAL

        elif self.state == FACE_GOAL:
            if abs(self.angle_goal) < ROTATE_MARGIN:
                self.state = SHOOT

    # Actions
    def face_pitch_center(self):
        """
        Face the center of the pitch. Alter the strategy state when necessary.
        :return: An action to be performed by the robot.
        """
        angle = self.bot.get_rotation_to_point(self.middle_x, self.middle_y)
        self._robot_controller.turn(angle)

    def face_goal(self):
        """
        Face the goal. Alter the strategy state when necessary.
        :return: An action to be performed by the robot.
        """
        angle_goal = self.bot.get_rotation_to_point(self.goal_x, self.goal_y)
        self._robot_controller.turn(angle_goal)

    def move_to_origin(self):
        """
        Move to the robot's origin. Alter the strategy state when necessary.
        :return: An action to be performed by the robot.
        """
        distance = self.bot.get_displacement_to_point(self.middle_x, self.middle_y)
        self._robot_controller.drive(distance, distance)


class Sleep(Strategy):
    def __init__(self, world, robot_controller):
        states = [NONE]
        action_map = {
            NONE: self.do_nothing
        }

        super(Sleep, self).__init__(world, robot_controller, states, action_map)

    def transition(self):
        pass


class PassBall(Strategy):
    def __init__(self, world, robot_controller):
        self._world = world
        self.bot = world.our_attacker
        self._robot_controller = robot_controller


        self.angle = 0
        self.freespot_x, self.freespot_y = (0, 0)
        self.snap_bot_y = 0

        states = [REORIENT_FREESPOT, REPOSITION, REORIENT_DEFENDER, OPEN_GRABBER, PASS]
        action_map = {
            REORIENT_FREESPOT: self.rotate_to_freespot,
            WAIT_REORIENT: self.do_nothing,
            REPOSITION: self.move_to_freespot,
            WAIT_REPOSITION: self.do_nothing,
            REORIENT_DEFENDER: self.rotate_to_defender,
            WAIT_REORIENT_DEFENDER: self.do_nothing,
            OPEN_GRABBER: self._robot_controller.open_grabber,
            WAIT_O_GRAB: self.do_nothing,
            PASS: self._robot_controller.kick
        }

        super(PassBall, self).__init__(world, robot_controller, states, action_map)

    def transition(self):

        #real freespot and angle values
        (real_freespot_x, real_freespot_y) = self.calc_freespot()
        real_realspot_angle = self.bot.get_rotation_to_point(self.freespot_x, self.freespot_y)
        real_defender_angle = self.bot.get_rotation_to_point(self._world.our_defender.x, self._world.our_defender.y)
        real_bot_y = self.bot.y

        print "PassBall: " + self.state

        if self.state == REORIENT_FREESPOT:
            # take snapshot of angle
            self.angle = real_realspot_angle

            print "\nROTATE TO FREESPOT\nangle: "+str(self.angle)
            print "margin: "+str(ROTATE_MARGIN)
            print "d/rotate: "+str(abs(self.angle < ROTATE_MARGIN))

            self.state = WAIT_REORIENT

        elif self.state == WAIT_REORIENT:
            if abs(self.angle) < ROTATE_MARGIN:
                self.state = REPOSITION

        elif self.state == REPOSITION:

            # take snapshot of freespot and robot
            (self.freespot_x, self.freespot_y) = (real_freespot_x, real_freespot_y)
            self.snap_bot_y = real_bot_y

            print "\nMOVE\nour_y: "+str(self.bot.y)
            print "freespot_y: "+str(self.freespot_y)
            print "dy: "+str(abs(self.snap_bot_y - self.freespot_y) < ROTATE_MARGIN)

            self.state = WAIT_REPOSITION

        elif self.state == WAIT_REPOSITION:
            if abs(self.snap_bot_y - self.freespot_y) < ROTATE_MARGIN:
                self.state = REORIENT_DEFENDER

        elif self.state == REORIENT_DEFENDER:

            # take snaphot of angle to defender
            self.angle = real_defender_angle

            print "\nROTATE TO DEFENDER\nangle: "+str(self.angle)
            print "margin: "+str(ROTATE_MARGIN)
            print "d/rotate: "+str(abs(self.angle < ROTATE_MARGIN))

            self.state = WAIT_REORIENT_DEFENDER

        elif self.state == WAIT_REORIENT_DEFENDER:
            if abs(self.angle) < ROTATE_MARGIN:
                self.state = OPEN_GRABBER

        if self.state == OPEN_GRABBER:

            # take snapshot of angle to defender
            self.angle = real_defender_angle
            print "\nPASSED WITH MARGIN\nangle: "+str(self.angle)+" radians from target"

            self.state = WAIT_O_GRAB

        if self.state == WAIT_O_GRAB:
            if self._robot_controller.grabber_open:
                self.state = PASS

    def rotate_to_freespot(self):
        angle = self.bot.get_rotation_to_point(self.freespot_x, self.freespot_y)
        self._robot_controller.turn(angle)

    def move_to_freespot(self):
        distance = self.bot.get_displacement_to_point(self.freespot_x, self.freespot_y)
        self._robot_controller.driver(distance, distance)

    def rotate_to_defender(self):
        angle = self.bot.get_rotation_to_point(self._world.our_defender.x, self._world.our_defender.y)
        self._robot_controller.turn(angle)

    def calc_freespot(self):
        (our_center_x, our_center_y) = self._world.pitch.zones[self.bot.zone].center()
        (their_center_x, their_center_y) = self._world.pitch.zones[self._world.their_attacker.zone].center()

        if self._world.their_attacker.y > their_center_y:
            freespot_y = (2.0/10) * self._world.pitch.height
        else:
            freespot_y = (8.0/10) * self._world.pitch.height

        freespot_x = int(our_center_x)

        return freespot_x, freespot_y