from utilities import *
from math import pi


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

    def get_status(self):
        return self._robot_controller.get_status


class Idle(Strategy):
    """
    The idle strategy is typically the initial strategy and should be returned
    to if the ball is not visible. This strategy has the robot return to its
    initial position.
    """

    def __init__(self, world, robot_controller):
        self.bot = world.our_attacker

        x, y = world.pitch.zones[self.bot.zone].center()

        self.middle_x = int(x)
        self.middle_y = int(y)

        self.angle_to_face = 0

        states = [REORIENT, WAIT_REORIENT, REPOSITION, WAIT_REPOSITION, IDLE]
        action_map = {
            REORIENT: self.face_pitch_center,
            WAIT_REORIENT: self.get_status,
            REPOSITION: self.move_to_origin,
            WAIT_REPOSITION: self.get_status,
            IDLE: self.do_nothing
        }

        super(Idle, self).__init__(world, robot_controller, states, action_map)

    def transition(self):

        bot_angle = self.bot.angle
        angle_to_target = self.bot.get_rotation_to_point(self.middle_x, self.middle_y)

        if self.state == REORIENT:
            self.angle_to_face = bot_angle + angle_to_target
            self.state == WAIT_REORIENT

        if self.state == WAIT_REORIENT:
            if not self._robot_controller.is_moving:
                if self.compare_angles(angle_to_target, 0.0):
                    self.state = REPOSITION
                else:
                    self.state = REORIENT

        elif self.state == REPOSITION:
            displacement = self.bot.get_displacement_to_point(self.middle_x, self.middle_y)
            if displacement < DISPLACEMENT_MARGIN:
                self.state = IDLE
            # else:
            #     self.reset()

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

        self.angle_to_face = 0

        states = [OPEN_GRABBER, WAIT_O_GRAB, REORIENT, WAIT_REORIENT, REPOSITION, WAIT_REPOSITION, CLOSE_GRABBER, WAIT_C_GRAB]
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

        bot_angle = self.bot.angle
        angle_to_target = self.bot.get_rotation_to_point(self.ball.x, self.ball.y)

        if self.state == OPEN_GRABBER:
            self.state = WAIT_O_GRAB

        elif self.state == WAIT_O_GRAB:
            if self._robot_controller.open_grabber:
                self.state = REORIENT

        elif self.state == REORIENT:
            self.angle_to_face = bot_angle + angle_to_target
            self.state = WAIT_REORIENT

        elif self.state == WAIT_REORIENT:
            if abs(self.angle_to_face - self.bot.angle) < ROTATE_MARGIN:
                if self.compare_angles(angle_to_target, 0.0):
                    self.state = REPOSITION
                # else:
                #     self.state = REORIENT

        elif self.state == REPOSITION:
            self.state = WAIT_REPOSITION

        elif self.state == WAIT_REPOSITION:
            if self.bot.can_catch_ball(self.ball):
                self.state = CLOSE_GRABBER
            # else:
            #     self.reset()

        elif self.state == CLOSE_GRABBER:
            if self.bot.can_catch_ball(self.ball):
                self.state = WAIT_C_GRAB
            # else:
            #     self.reset()

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

        self.angle_to_face = 0

        states = [OPEN_GRABBER, WAIT_O_GRAB, REORIENT_FREESPOT, WAIT_REORIENT_FREESPOT, REPOSITION, WAIT_REPOSITION, REORIENT_PASSER, WAIT_REORIENT_PASSER, IDLE]
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

        bot_angle = self.bot.angle
        angle_to_freespot = self.bot.get_rotation_to_point(self.freespot_x, self.freespot_y)
        angle_to_passer = self.bot.get_rotation_to_point(self.passer.x, self.passer.y)

        # Open the grabber
        if self.state == OPEN_GRABBER:
            self.state == WAIT_O_GRAB

        if self.state == WAIT_O_GRAB:
            if self._robot_controller.grabber_open:
                self.state = REORIENT_FREESPOT

        # Rotate to face the "freespot" (point at center of our zone)
        elif self.state == REORIENT_FREESPOT:
            self.angle_to_face = bot_angle + angle_to_freespot
            self.state = WAIT_REORIENT_FREESPOT

        elif self.state == WAIT_REORIENT_FREESPOT:
            if abs(self.angle_to_face - self.bot.angle) < ROTATE_MARGIN:
                if self.compare_angles(angle_to_freespot, 0):
                    self.state = REPOSITION
                # else:
                #     self.state = REORIENT_FREESPOT

        # Move to the freespot
        elif self.state == REPOSITION:
            self.state = WAIT_REPOSITION

        elif self.state == WAIT_REPOSITION:
            # if on freespot
            displacement = self.bot.get_displacement_to_point(self.freespot_x, self.freespot_y)
            if displacement < DISPLACEMENT_MARGIN:
                self.state = REORIENT_PASSER

        # Rotate to face our passer, and wait
        elif self.state == REORIENT_PASSER:
            self.angle_to_face = self.bot.angle + angle_to_passer
            self.state = WAIT_REORIENT_PASSER

        elif self.state == WAIT_REORIENT_PASSER:
            if abs(self.angle_to_face - self.bot.angle) < ROTATE_MARGIN:
                if self.compare_angles(angle_to_passer, 0.0):
                    self.state = IDLE
                # else:
                #     self.REORIENT_FREESPOT

    def aim_towards_freespot(self):
        angle = self.bot.get_rotation_to_point(self.freespot_x, self.freespot_y)
        self._robot_controller.turn(angle)

    def move_towards_freespot(self):
        distance = self.bot.get_displacement_to_point(self.freespot_x, self.freespot_y)
        self._robot_controller(distance, distance)

    def aim_towards_passer(self):
        angle = self.bot.get_rotation_to_point(self.passer.x, self.passer.y)
        self._robot_controller.turn(angle)


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

        self.freespot_x, self.freespot_y = self.calc_freespot()
        self.defender_x, self.defender_y = (self._world.our_defender.x, self._world.our_defender.y)
        self.snap_bot_y = self.bot.y
        self.angle = self.bot.get_rotation_to_point(self.freespot_x, self.freespot_y)

        states = [INIT_VARS, REORIENT_FREESPOT, WAIT_REORIENT, REPOSITION, WAIT_REPOSITION, REORIENT_DEFENDER, WAIT_REORIENT_DEFENDER, OPEN_GRABBER, WAIT_O_GRAB, PASS]
        action_map = {
            INIT_VARS: self.do_nothing(),
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
        #print self.state
        #real freespot and angle values
        (real_freespot_x, real_freespot_y) = self.calc_freespot()
        (real_defender_x, real_defender_y) = (self._world.our_defender.x, self._world.our_defender.y)
        real_realspot_angle = self.bot.get_rotation_to_point(self.freespot_x, self.freespot_y)
        real_defender_angle = self.bot.get_rotation_to_point(self._world.our_defender.x, self._world.our_defender.y)
        real_bot_y = self.bot.y


        if self.state == INIT_VARS:
            (self.freespot_x, self.freespot_y) = (real_freespot_x, real_freespot_y)
            self.state = REORIENT_FREESPOT

        elif self.state == REORIENT_FREESPOT:
            # take snapshot of freespot cords
            print "\n1"

            print "freespot: ("+str(self.freespot_x)+", "+str(self.freespot_y)+")"
            print "robot: ("+str(self.bot.x)+", "+str(self.bot.y)+")"

            print "\nROTATE TO FREESPOT\nangle: "+str(self.angle*180/pi)+"deg"
            print "margin: "+str(ROTATE_MARGIN)
            print "d/rotate: "+str(abs(self.angle < ROTATE_MARGIN))

            self.state = WAIT_REORIENT

        elif self.state == WAIT_REORIENT:
            self.angle = self.bot.get_rotation_to_point(self.freespot_x, self.freespot_y)
            #print "Rotating to Freespot: "+str(self.angle)

            if abs(self.angle) < ROTATE_MARGIN:
                self._robot_controller.get_status()

                if self.compare_angles(self.angle, real_realspot_angle):
                    self.state = REPOSITION
                elif not self._robot_controller.is_moving:
                    print "<RETRY>"
                    self.reset()

        elif self.state == REPOSITION:

            # take snapshot of freespot and robot
            (self.freespot_x, self.freespot_y) = (real_freespot_x, real_freespot_y)
            self.snap_bot_y = real_bot_y

            print "\nMOVE\nour_y: "+str(self.bot.y)
            print "freespot_y: "+str(self.freespot_y)
            print "dy: "+str(abs(self.snap_bot_y - self.freespot_y) < ROTATE_MARGIN)

            self.state = WAIT_REPOSITION

        elif self.state == WAIT_REPOSITION:
            #print "Repositioning to Freespot: "+str(abs(real_bot_y - self.freespot_y))
            if abs(real_bot_y - self.freespot_y) < DISPLACEMENT_MARGIN:
                self.state = REORIENT_DEFENDER

        elif self.state == REORIENT_DEFENDER:

            # take snaphot of defender cords
            (self.defender_x, self.defender_y) = (real_defender_x, real_defender_y)

            print "\nROTATE TO DEFENDER\nangle: "+str(self.angle*180/pi)+"deg"
            print "margin: "+str(ROTATE_MARGIN)
            print "d/rotate: "+str(abs(self.angle < ROTATE_MARGIN))

            self.state = WAIT_REORIENT_DEFENDER

        elif self.state == WAIT_REORIENT_DEFENDER:
            self._robot_controller.get_status()

            self.angle = self.bot.get_rotation_to_point(self.defender_x, self.defender_y)
            #print "Rotating: "+str(self.angle)

            if abs(self.angle) < ROTATE_MARGIN:
                if self.compare_angles(self.angle, real_defender_angle):
                    self.state = OPEN_GRABBER
                elif not self._robot_controller.is_moving:
                    print "<RETRY>"
                    self.reset()

        elif self.state == OPEN_GRABBER:
            #todo: FIGURE OUT WHY KICK DOES NOT WORK NICELY BEYOND THIS POINT.
            self.state = WAIT_O_GRAB

        elif self.state == WAIT_O_GRAB:
            if self._robot_controller.grabber_open:
                self.state = PASS

        elif self.state == PASS:
            print "\n--------------PASSED BALL WITH MARGIN\nangle: "+str(real_defender_angle)+" radians from target"
            self.state = IDLE

    def rotate_to_freespot(self):
        angle = self.bot.get_rotation_to_point(self.freespot_x, self.freespot_y)
        self._robot_controller.turn(angle)

    def move_to_freespot(self):
        distance = self.bot.get_displacement_to_point(self.freespot_x, self.freespot_y)
        self._robot_controller.drive(distance, distance)

    def rotate_to_defender(self):
        angle = self.bot.get_rotation_to_point(self._world.our_defender.x, self._world.our_defender.y)
        self._robot_controller.turn(angle)

    def calc_freespot(self):
        (our_center_x, our_center_y) = self._world.pitch.zones[self.bot.zone].center()
        (their_center_x, their_center_y) = self._world.pitch.zones[self._world.their_attacker.zone].center()

        if self._world.their_attacker.y > their_center_y:
            freespot_y = (2.5/10) * self._world.pitch.height
        else:
            freespot_y = (7.5/10) * self._world.pitch.height

        freespot_x = int(our_center_x)

        return freespot_x, freespot_y