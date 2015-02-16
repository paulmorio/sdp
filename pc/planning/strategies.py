from utilities import *


class Strategy(object):
    """
    A base class on which other strategies should be built. Sets up the
    interface used by the Planner class.
    """
    def __init__(self, world, states, action_map):
        self._STATES = states
        self._STATE_ACTION_MAP = action_map
        assert(self.all_states_mapped())
        self._world = world
        self._state = self._STATES[0]

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


class Idle(Strategy):
    """
    The idle strategy is typically the initial strategy and should be returned
    to if the ball is unreachable. This strategy has the robot return to its
    initial position.
    """

    def __init__(self, world):
        states = [REPOSITION, REORIENT, IDLE]
        action_map = {
            REPOSITION: self.move_to_origin,
            REORIENT: self.face_pitch_center,
            IDLE: self.do_nothing
        }

        super(Idle, self).__init__(world, states, action_map)

    # Actions
    def move_to_origin(self):
        """
        Move to the robot's origin.
        :return: An action to be performed by the robot.
        """
        pass

    def face_pitch_center(self):
        """
        Face the center of the pitch - ready for kick-off
        :return: An action to be performed by the robot.
        """
        pass



class Intercept(Strategy):
    pass


class GetBall(Strategy):
    pass


class ShootBall(Strategy):
    pass


class PassBall(Strategy):
    pass


