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
        assert (profile in ['attacker', 'penalty'])
        self.world = world
        self._profile = profile
        self.robot_mdl = world.our_attacker
        self.robot_ctl = robot_ctl

        # Strategy dictionaries return a strategy given a state.
        self._strategy_map = {}
        self.update_strategy_map()

        # Choose initial strategy
        self.state = BALL_NOT_VISIBLE
        self.strategy = None
        self.update_strategy()

    @property
    def planner_state_string(self):
        return self.state.replace('_', ' ').capitalize() + '.'

    @property
    def strategy_state_string(self):
        return self.strategy.state.replace('_', ' ').capitalize() + '.'

    @property
    def profile(self):
        return self._profile

    @profile.setter
    def profile(self, new_profile):
        self._profile = new_profile
        self.state = BALL_NOT_VISIBLE
        self.update_strategy_map()

    # Defining strategy map depending on the profile
    def update_strategy_map(self):
        if self.profile == 'attacker':
            self._strategy_map = {
                BALL_NOT_VISIBLE: Idle(self.world, self.robot_ctl),
                GETTING_BALL: GetBall(self.world, self.robot_ctl),
                POSSESSION: ShootGoal(self.world, self.robot_ctl),
                DEFENDING: Defend(self.world, self.robot_ctl),
                INTERCEPT: Intercept(self.world, self.robot_ctl),
                AWAITING_PASS: AwaitPass(self.world, self.robot_ctl)
            }
        elif self.profile == 'penalty':
            self._strategy_map = {
                BALL_NOT_VISIBLE: Idle(self.world, self.robot_ctl),
                POSSESSION: PenaltyKick(self.world, self.robot_ctl)
            }

    def plan(self):
        """
        Update the planner and strategy states before acting.
        """
        if self.profile == 'attacker':
            self.attacker_transition()
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
            # Their defender has the ball
            if self.world.can_catch_ball(self.world.their_defender):
                self.state = DEFENDING
            # Either rebound or a pass
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
            if (self.state == DEFENDING or self.state == INTERCEPT) \
                    and self.world.ball.velocity > 4:  # TODO tweak
                self.state = INTERCEPT
            else:
                self.state = GETTING_BALL

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

    def penalty_transition(self):
        """
        IMPORTANT:  Ball must be grabbed before starting up robot
                    Otherwise it will transition back to attacker state!

        Update the planner state and strategy given the current state of the
        world model.

        For the penalty profile
        """
        # Holding the ball, ready to take penalty
        # if self.world.can_catch_ball(self.robot_mdl):
        #     self.state = POSSESSION
        #self.robot_ctl._update_state_bits
        if self.robot_ctl.ball_grabbed:
            self.state = POSSESSION

        # NOT Holding the ball anymore (kicked!)
        else:
            print "ball_grabbed: "+str(self.robot_ctl.ball_grabbed)
            print "PROFILE CHANGE TO ATTACKER"
            # Set profile back to attacker
            self.profile = 'attacker'

        self.update_strategy()
