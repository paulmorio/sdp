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

    def pass_ball(self):
        """
        Pass the ball: shoot with low strength?
        """
        self._robot_controller.command(PASS)




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

        self.friendly_space = 70
        self.rotate_margin = 0.50

        states = [OPEN_GRABBER, REORIENT, REPOSITION, CLOSE_GRABBER]
        action_map = {
            OPEN_GRABBER: self.open_grabber,
            REORIENT: self.aim_towards_ball,
            REPOSITION: self.move_towards_ball,
            CLOSE_GRABBER: self.close_grabber
        }

        super(GetBall, self).__init__(world, robot_controller, states, action_map)

    def transition(self):
        # IF NOT FACING BALL
        angle_to_turn_to = self.bot.get_rotation_to_point(self.ball.x, self.ball.y)

        if self.state == OPEN_GRABBER:
            if self.bot.catcher == OPENED:
                self.state = REORIENT

        elif self.state == REORIENT:
            if abs(angle_to_turn_to) < self.rotate_margin:
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
    The ball is inside our defender's zone, therefore: position ourselves to receive ball
    Rotate towards un-interrupted-pass position (freespot), move towards it, rotate towards defender
    """
    def __init__(self, world, robot_controller):

        states = [OPEN_GRABBER, REORIENT_FREESPOT, REPOSITION, REORIENT_DEFENDER]
        action_map = {
            OPEN_GRABBER: self.open_grabber,
            REORIENT_FREESPOT: self.aim_towards_freespot,
            REPOSITION: self.move_towards_freespot,
            REORIENT_DEFENDER: self.aim_towards_defender
        }

        super(CatchBall, self).__init__(world, robot_controller, states, action_map)

    def transition(self):
        pass

    def aim_towards_freespot(self):
        pass

    def move_towards_freespot(self):
        pass

    def aim_towards_defender(self):
        pass

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

        self.bot = world.our_attacker
        self.world = world

        (self.freespot_x, self.freespot_y) = self.calc_freespot()

        self.rotate_margin = 0.10
        self.distance_margin = 40

        states = [REORIENT_FREESPOT, REPOSITION, REORIENT_DEFENDER, OPEN_GRABBER, PASS]
        action_map = {
            REORIENT_FREESPOT: self.rotate_to_freespot,
            REPOSITION: self.move_to_freespot,
            REORIENT_DEFENDER: self.rotate_to_defender,
            OPEN_GRABBER: self.open_grabber,
            PASS: self.pass_ball
        }

        super(PassBall, self).__init__(world, robot_controller, states, action_map)

    def transition(self):
        (self.freespot_x, self.freespot_y) = self.calc_freespot()

        print self.state

        if self.state == REORIENT_FREESPOT:
            angle = self.bot.get_rotation_to_point(self.freespot_x, self.freespot_y)
            print "\nROTATE TO FREESPOT\nangle: "+str(angle)
            print "margin: "+str(self.rotate_margin)
            print "d/rotate: "+str(abs(angle < self.rotate_margin))

            if abs(angle) < self.rotate_margin:
                self.state = REPOSITION

        elif self.state == REPOSITION:
            print "\nMOVE\nour_y: "+str(self.bot.y)
            print "freespot_y: "+str(self.freespot_y)
            print "dy: "+str(abs(self.bot.y - self.freespot_y) < self.distance_margin)

            if abs(self.bot.y - self.freespot_y) < self.distance_margin:
                self.state = REORIENT_DEFENDER

        elif self.state == REORIENT_DEFENDER:
            angle = self.bot.get_rotation_to_point(self.world.our_defender.x, self.world.our_defender.y)
            print "\nROTATE TO DEFENDER\nangle: "+str(angle)
            print "margin: "+str(self.rotate_margin)
            print "d/rotate: "+str(abs(angle < self.rotate_margin))

            if abs(angle) < self.rotate_margin:
                self.state = OPEN_GRABBER

        if self.state == OPEN_GRABBER:
            angle = self.bot.get_rotation_to_point(self.world.our_defender.x, self.world.our_defender.y)
            print "\nPASSED WITH MARGIN\nangle: "+str(angle)+" radians from target"

            if self.bot.catcher == OPENED:
                self.state = PASS



    def rotate_to_freespot(self):
        angle = self.bot.get_rotation_to_point(self.freespot_x, self.freespot_y)
        self.rotate(angle)

    def move_to_freespot(self):
        distance = self.bot.get_displacement_to_point(self.freespot_x, self.freespot_y)
        self.move(distance)

    def rotate_to_defender(self):
        angle = self.bot.get_rotation_to_point(self.world.our_defender.x, self.world.our_defender.y)
        self.rotate(angle)

    def calc_freespot(self):
        (our_center_x, our_center_y) = self.world.pitch.zones[self.bot.zone].center()
        (their_center_x, their_center_y) = self.world.pitch.zones[self.world.their_attacker.zone].center()

        if self.world.their_attacker.y > their_center_y:
            freespot_y = (2.0/10) * self.world.pitch.height
        else:
            freespot_y = (8.0/10) * self.world.pitch.height

        freespot_x = int(our_center_x)

        return (freespot_x, freespot_y)


