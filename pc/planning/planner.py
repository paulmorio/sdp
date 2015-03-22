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
            self._strategy_map = {
                BALL_NOT_VISIBLE: Idle(self.world, self.robot_ctl),
                GETTING_BALL: GetBall(self.world, self.robot_ctl),
                POSSESSION: ShootGoal(self.world, self.robot_ctl),
                INTERCEPT: Intercept(self.world, self.robot_ctl),
                DEFENDING: Defend(self.world, self.robot_ctl),
                AWAITING_PASS: AwaitPass(self.world, self.robot_ctl)
            }
        elif self.profile == 'ms3':
            self._strategy_map = {
                BALL_NOT_VISIBLE: Idle(self.world, self.robot_ctl),
                GETTING_BALL: GetBall(self.world, self.robot_ctl),
                POSSESSION: PassBall(self.world, self.robot_ctl),
                BALL_NOT_IN_OUR_ZONE: FaceBall(self.world, self.robot_ctl)
            }
        elif self.profile == 'penalty':
            self._strategy_map = {
                BALL_NOT_VISIBLE: Idle(self.world, self.robot_ctl),
                POSSESSION: PenaltyKick(self.world, self.robot_ctl)
            }

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
        new_strategy = self._strategy_map[self.state]
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
        # Successfully grabbed ball, who cares what area it's in?
        if self.robot_ctl.ball_grabbed:
            self.state = POSSESSION

        # Ball is in their defender's area
        elif self.world.ball_in_area([self.world.their_defender]):
            # Assume their def has ball, stalk the defender's target
            # TODO add estimated catch areas to opposition bots
            if self.world.can_catch_ball(self.world.their_defender):
                self.state = DEFENDING
            # Ball is travelling. Either rebound or kick from defender
            else:
                self.state = INTERCEPT

        # Ball in our defender's area
        elif self.world.ball_in_area([self.world.our_defender]):
            # Assume our defender has the ball
            if self.world.can_catch_ball(self.world.our_defender):
                self.state = AWAITING_PASS
            # Could be a rebound, if so then prepare to intercept
            elif not self.state == AWAITING_PASS:
                self.state = INTERCEPT

        # Ball in our margin
        elif self.world.ball_in_area([self.robot_mdl]):
            # The ball is heading at us (hopefully) or is slow
            # TODO tune velocity threshold, ball smoothing (kalman)
            # TODO distance from grabber center to ball
            if self.state == AWAITING_PASS or self.world.ball.velocity < 2:
                self.state = GETTING_BALL
            else:  # Stay in intercept mode until the ball is slow enough
                self.state = INTERCEPT

        # Ball in their attacker's margin
        elif self.world.ball_in_area([self.world.their_attacker]):
            # If we're awaiting a pass then remain as such
            if self.state == AWAITING_PASS:
                pass
            # Ball is not a pass, could be a rebound
            else:
                self.state = INTERCEPT

        # Ball is not visible or is between zones (calibrate properly?)
        else:
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
            self.state = GETTING_BALL

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