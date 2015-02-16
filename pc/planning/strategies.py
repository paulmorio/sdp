from utilities import *


class Strategy(object):
    """
    A base class on which other strategies should be built. Sets up the
    interface used by the Planner class.
    """
    def __init__(self, world, states):
        self._world = world
        self._states = states
        self._state = states[0]

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
        assert (new_state in self._states)
        self._state = new_state

    def reset(self):
        """Reset the Strategy object to its initial state."""
        self._state = self._states[0]

    def final_state(self):
        """Return True if the current state is final."""
        return self._state == self._states[-1]

    def get_plan(self):
        """Return the next robot action"""
        return None

    # Actions
    def do_nothing(self):
        """Tell the planner that there is no new action to perform."""
        return None


class Idle(Strategy):
    """
    The idle strategy is typically the initial strategy and should be returned
    to if the ball is unreachable. This strategy has the robot return to its
    initial position.
    """
    STATES = [REPOSITION, REORIENT, IDLE]

    def __init__(self, world):
        super(Idle, self).__init__(world, self.STATES)

        # Given the current state, return the method to be run
        self.STATE_ACTION_MAP = {
            REPOSITION: self.move_to_origin,
            REORIENT: self.face_pitch_center,
            IDLE: do_nothing
        }

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


def do_nothing():
    """
    Dummy action for strategies - usually used when in final state.
    :return: None
    """
    return None