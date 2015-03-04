from strategies import *
from utilities import *


class Planner(object):

    def __init__(self, world, robot_ctl, profile):
        """
        Create a planner object.
        :param world: World model object from pc.models.worldmodel.
        :type world: World
        :param robot_ctl: Robot control object from pc.robot
        :type robot_ctl: Robot
        :param profile: Planning profile.
        :type profile: str
        """
        assert (profile in ['ms3'])
        self._world = world
        self._profile = profile
        self._robot_mdl = world.our_attacker
        self._robot_ctl = robot_ctl

        # Strategy dictionaries return a strategy given a state.
        if self._profile == 'ms3':
            self._strat_map = {
                BALL_NOT_VISIBLE: Idle(self._world, self._robot_ctl),
                BALL_OUR_ZONE: GetBall(self._world, self._robot_ctl),
                POSSESSION: PassBall(self._world, self._robot_ctl),
                BALL_NOT_IN_OUR_ZONE: FaceBall(self._world, self._robot_ctl)}

        # Choose initial strategy
        self._state = BALL_NOT_VISIBLE
        self._strategy = None
        self.update_strategy()

    def plan(self):
        """
        Update the planner and strategy states before acting.
        """
        self.ms3_transition()
        self._strategy.act()

    def update_strategy(self):
        """
        Set the appropriate strategy given the current state.
        If you wish to switch to a 'fresh' copy of the current
        strategy then you must explicitly call its reset method.
        """
        new_strategy = self._strat_map[self._state]
        if new_strategy is not self._strategy:
            if self._strategy is not None:
                self._strategy.reset()
            self._strategy = new_strategy

    def ms3_transition(self):
        """
        Update the planner state and strategy given the current state of the
        world model.

        For the attacker profile.
        """
        # Successfully grabbed ball
        if self._robot_ctl.ball_grabbed:
            self._state = POSSESSION

        # If ball is in our margin - move to possession state if ball grabbed
        elif self._world.ball_in_area([self._robot_mdl]):
            self._state = BALL_OUR_ZONE

        # If the ball is not visible
        elif not self._world.ball_in_play():
            self._state = BALL_NOT_VISIBLE

        # Ball in play but not in our margin
        else:
            self._state = BALL_NOT_IN_OUR_ZONE

        self.update_strategy()
