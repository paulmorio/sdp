from utilities import *
from math import pi


class Strategy(object):
    """
    A base class on which other strategies should be built. Sets up the
    interface used by the Planner class.
    """
    def __init__(self, world, robot_ctl, state_map):
        self.state_map = state_map
        self._world = world
        self._robot_controller = robot_ctl
        self._state = self.state_map.keys()[0]
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
        assert (new_state in self.state_map.keys())
        self._state = new_state

    def reset(self):
        """Reset the Strategy object to its initial state."""
        self._state = self.state_map.keys()[0]

    def final_state(self):
        """Return True if the current state is final."""
        return self._state == self.state_map.keys()[-1]

    def act(self):
        """Call the appropriate method given the state map and current state."""
        self.state_map[self.state]()


class Idle(Strategy):
    """
    The idle strategy has the robot do nothing.
    Intended use is when the ball is not visible or not reachable by the robot.
    """
    def __init__(self):
        _STATE_MAP = {IDLE: self.do_nothing}
        super(Idle, self).__init__(None, None, _STATE_MAP)

    def do_nothing(self):
        pass


class GetBall(Strategy):
    """
    Have the robot move to the ball then grab it.
    Intended use is when the ball is in our robot's area.
    """
    def __init__(self, world, robot_ctl):
        _STATE_MAP = {}
        super(GetBall, self).__init__(world, robot_ctl, _STATE_MAP)


class PassBall(Strategy):
    """
    Have the robot find a path and pass to the defending robot.
    Intended use is when the ball is in our possession.
    """
    def __init__(self, world, robot_ctl):
        _STATE_MAP = {}
        super(PassBall, self).__init__(world, robot_ctl, _STATE_MAP)
