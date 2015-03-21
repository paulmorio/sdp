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
        assert (profile in ['attacker', 'ms3', 'penalty'])
        self.world = world
        self.profile = profile
        self.robot_mdl = world.our_attacker
        self.robot_ctl = robot_ctl

        # Strategy dictionaries return a strategy given a state.
        if self.profile == 'attacker':
            self._strat_map = {
                BALL_NOT_VISIBLE: Idle(self.world, self.robot_ctl),
                BALL_OUR_ZONE: GetBall(self.world, self.robot_ctl),
                POSSESSION: ShootGoal(self.world, self.robot_ctl),
                BALL_OUR_DEFENDER_ZONE: Idle(self.world, self.robot_ctl),
                BALL_THEIR_ATTACKER_ZONE: Idle(self.world, self.robot_ctl),
                BALL_THEIR_DEFENDER_ZONE: Idle(self.world, self.robot_ctl),
                AWAITING_PASS: Idle(self.world, self.robot_ctl)
            }
        elif self.profile == 'ms3':
            self._strat_map = {
                BALL_NOT_VISIBLE: Idle(self.world, self.robot_ctl),
                BALL_OUR_ZONE: GetBall(self.world, self.robot_ctl),
                POSSESSION: PassBall(self.world, self.robot_ctl),
                BALL_NOT_IN_OUR_ZONE: FaceBall(self.world, self.robot_ctl)}
        elif self.profile == 'penalty':
            self._strat_map = {
                BALL_NOT_VISIBLE: Idle(self.world, self.robot_ctl),
                POSSESSION: PenaltyKick(self.world, self.robot_ctl)}

        # Choose initial strategy
        self.state = BALL_NOT_VISIBLE
        self.strategy = None
        self.update_strategy()

    def plan(self):
        """
        Update the planner and strategy states before acting.
        """
        if self.profile == 'attacker':
            self.attacker_transition()
        elif self.profile == 'ms3':
            self.ms3_transition()
        elif self.profile == 'penalty':
            self.penalty_transition()

        self.strategy.act()  # Strategy transition, queue robot action
        self.robot_ctl.act()  # Send the queued action if possible

    def update_strategy(self):
        """
        Set the appropriate strategy given the current state.
        If you wish to switch to a 'fresh' copy of the current
        strategy then you must explicitly call its reset method.
        """
        new_strategy = self._strat_map[self.state]
        if new_strategy is not self.strategy:
            if self.strategy is not None:
                self.strategy.reset()
            else:
                self.strategy = new_strategy

    def attacker_transition(self):
        """
        Generic attacker transition model.

        Updates the planner state and current strategy based on the world state
        """
        # Successfully grabbed ball
        if self.robot_ctl.ball_grabbed:
            self.state = POSSESSION

        # If the ball is in their defender's margin, shadow the def/ball
        elif self.world.ball_in_area([self.world.their_defender]):
            self.state = BALL_THEIR_DEFENDER_ZONE

        # If ball is in our margin, go get it
        elif self.world.ball_in_area([self.robot_mdl]):
            self.state = BALL_OUR_ZONE

        # Awaiting pass, ball not yet in our area
        elif self.state == AWAITING_PASS:
            pass

        # If the ball is in our defender's margin, await pass or rebound
        elif self.world.ball_in_area([self.world.our_defender]):
            if self.world.can_catch_ball(self.world.our_defender):
                self.state = AWAITING_PASS
            else:
                self.state = BALL_OUR_DEFENDER_ZONE

        # The ball is in their attacker's margin and we're not awaiting a pass
        elif self.world.ball_in_area([self.world.their_attacker]):
            self.state = BALL_THEIR_ATTACKER_ZONE  # Await rebound

        # If the ball is not visible, do nothing
        elif not self.world.ball_in_play():
            self.state = BALL_NOT_VISIBLE

        self.update_strategy()

    def ms3_transition(self):
        """
        Update the planner state and strategy given the current state of the
        world model.

        For the attacker (ms3) profile.
        """
        # Successfully grabbed ball
        if self.robot_ctl.ball_grabbed:
            self.state = POSSESSION

        # If ball is in our margin
        elif self.world.ball_in_area([self.robot_mdl]):
            self.state = BALL_OUR_ZONE

        # If the ball is not visible
        elif not self.world.ball_in_play():
            self.state = BALL_NOT_VISIBLE

        # Ball in play but not in our margin
        else:
            self.state = BALL_NOT_IN_OUR_ZONE

        self.update_strategy()

    def penalty_transition(self):
        """
        Update the planner state and strategy given the current state of the
        world model.

        For the penalty profile
        """
        # Holding the ball
        if self.robot_ctl.ball_grabbed:
            self.state = POSSESSION

        # NOT Holding the ball
        else:
            self.state = BALL_NOT_VISIBLE

        self.update_strategy()