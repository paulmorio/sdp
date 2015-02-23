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
        return None

    ###################################################################
    def open_grabber(self):
        """
        Open the grabber, and set the bot's catcher status to open
        """
        if not self._bot.catcher == OPENED:
            self._robot_controller.command(OPEN_GRABBER)
            self._bot.catcher = OPENED
            #print "GRABBER: OPEN"

    def close_grabber(self):
        """
        Close the grabber, and set the bot's catcher status to closed
        """
        if not self._bot.catcher == CLOSED:
            self._robot_controller.command(CLOSE_GRABBER)
            self._bot.catcher = CLOSED
            #print "GRABBER: CLOSED"

    def rotate(self, angle):
        """
        ROTATE THE ROBOT angle RADIANS
        """
        #self._robot_controller.command(ROTATE, angle)
        #print "Rotating "+str(angle)+" radians."
        pass

    def move(self, distance):
        """
        MOVE THE ROBOT distance CM
        """
        #self._robot_controller.command(MOVE, distance)
        #print "Moving "+str(distance)+"cm."
        pass




class Idle(Strategy):
    """
    The idle strategy is typically the initial strategy and should be returned
    to if the ball is unreachable. This strategy has the robot return to its
    initial position.
    """

    def __init__(self, world, robot_controller):

        states = [REPOSITION, REORIENT, IDLE]
        action_map = {
            REPOSITION: self.move_to_origin,
            REORIENT: self.face_pitch_center,
            IDLE: self.do_nothing
        }

        super(Idle, self).__init__(world, robot_controller, states, action_map)

    def transition(self):
        pass

    # Actions
    def move_to_origin(self):
        """
        Move to the robot's origin. Alter the strategy state when necessary.
        :return: An action to be performed by the robot.
        """
        pass

    def face_pitch_center(self):
        """
        Face the center of the pitch. Alter the strategy state when necessary.
        :return: An action to be performed by the robot.
        """
        pass


class GetBall(Strategy):
    """
    The ball is inside of our attacker's zone, therefore: try to get it
    first open the grabber, aim towards ball, move towards it, and grab it
    """
    def __init__(self, world, robot_controller):
        self.ball = world._ball
        self.bot = world.our_attacker

        self.rotate_margin = 0.5  # TODO: tune value

        states = [OPEN_GRABBER, REORIENT, REPOSITION, CLOSE_GRABBER]
        action_map = {
            OPEN_GRABBER: self.open_grabber,
            REORIENT: self.aim_towards_ball,
            REPOSITION: self.move_towards_ball,
            CLOSE_GRABBER: self.close_grabber
        }

        super(GetBall, self).__init__(world, robot_controller, states, action_map)

    def transition(self):
        print self.state
        angle = self.bot.get_rotation_to_point(self.ball.x, self.ball.y)

        if self.state == OPEN_GRABBER:
            if self.bot.catcher == OPENED:
                self.state = REORIENT

        elif self.state == REORIENT:
            if abs(angle) < self.rotate_margin:
                self.state = REPOSITION

        elif self.state == REPOSITION:
            if self.bot.can_catch_ball(self.ball):
                self.state = CLOSE_GRABBER
            else:
                self.reset()

    def aim_towards_ball(self):
        angle = self.bot.get_rotation_to_point(self.ball.x, self.ball.y)
        self.rotate(angle)

    def move_towards_ball(self):
        distance = self.bot.get_displacement_to_point(self.ball.x, self.ball.y)
        self.move(distance)


class CatchBall(Strategy):
    """
    The lazy, no-communication method:
    Sit in the middle of our zone, with the grabber open, facing our teammate
    """
    def __init__(self, world, robot_controller):
        self.bot = world.our_defender
        self.passer = world.our_attacker

        x, y = world.pitch.zones[self.bot.zone].center()

        self.freespot_x = int(x)
        self.freespot_y = int(y)

        self.rotate_margin = 0.5  # TODO: tune value
        self.displacement_margin = 30  # TODO: tune value

        states = [OPEN_GRABBER, REORIENT_FREESPOT, REPOSITION, REORIENT_PASSER, IDLE]
        action_map = {
            OPEN_GRABBER: self.open_grabber,
            REORIENT_FREESPOT: self.aim_towards_freespot,
            REPOSITION: self.move_towards_freespot,
            REORIENT_PASSER: self.aim_towards_passer,
            IDLE: self.do_nothing
        }

        super(CatchBall, self).__init__(world, robot_controller, states, action_map)

    def transition(self):
        print self.state

        angle = self.bot.get_rotation_to_point(self.freespot_x, self.freespot_y)

        # Open the grabber
        if self.state == OPEN_GRABBER:
            if self.bot.catcher == OPENED:
                self.state = REORIENT_FREESPOT

        # Rotate to face the "freespot" (point at center of our zone)
        elif self.state == REORIENT_FREESPOT:
            angle = self.bot.get_rotation_to_point(self.freespot_x, self.freespot_y)
            if abs(angle) < self.rotate_margin:
                self.state = REPOSITION

        # Move to the freespot
        elif self.state == REPOSITION:
            # if on freespot
            displacement = self.bot.get_displacement_to_point(self.freespot_x, self.freespot_y)
            if displacement < self.displacement_margin:
                self.state = REORIENT_PASSER

        # Rotate to face our passer, and wait
        elif self.state == REORIENT_PASSER:
            angle = self.bot.get_rotation_to_point(self.passer.x, self.passer.y)
            if abs(angle) < self.rotate_margin:
                self.state = IDLE
            else:
                self.state = REORIENT_PASSER

    def aim_towards_freespot(self):
        angle = self.bot.get_rotation_to_point(self.freespot_x, self.freespot_y)
        self.rotate(angle)

    def move_towards_freespot(self):
        distance = self.bot.get_displacement_to_point(self.freespot_x, self.freespot_y)
        self.move(distance)

    def aim_towards_passer(self):
        angle = self.bot.get_rotation_to_point(self.passer.x, self.passer.y)
        self.rotate(angle)


class Confuse(Strategy):
    """
    The ball is in the enemy attacker's zone. Basically there's nothing we can do here.
    """
    def __init__(self, world, robot_controller):
        states = [OPEN_GRABBER]
        action_map = {
            OPEN_GRABBER: self.open_grabber
        }

        super(Confuse, self).__init__(world, robot_controller, states, action_map)

    def transition(self):
        pass

class Intercept(Strategy):
    """
    The ball is inside the enemy defender's zone
    """
    def __init__(self, world, robot_controller):
        states = [OPEN_GRABBER]
        action_map = {
            OPEN_GRABBER: self.open_grabber
        }

        super(Intercept, self).__init__(world, robot_controller, states, action_map)

    def transition(self):
        pass

class ShootBall(Strategy):
    def __init__(self, world, robot_controller):
        states = [NONE]
        action_map = {
            NONE: self.dummy
        }

        super(ShootBall, self).__init__(world, robot_controller, states, action_map)

    def transition(self):
        pass

    def dummy(self):
        print "I'm a dummy!"

class PassBall(Strategy):
    def __init__(self, world, robot_controller):
        states = [OPEN_GRABBER]
        action_map = {
            OPEN_GRABBER: self.open_grabber
        }

        super(PassBall, self).__init__(world, robot_controller, states, action_map)

    def transition(self):
        pass


