from strategies import *
from utilities import *


class Planner(object):

    def __init__(self, world, robot_controller, profile):
        """
        Create a planner object.
        :param world: World model object from pc.models.worldmodel.
        :type world: World
        :param robot_controller: Robot control object from pc.robot
        :type robot_controller: Robot
        :param profile: Planning profile.
        :type profile: str
        """
        assert (profile in ['attacker', 'defender'])
        self._world = world
        self._profile = profile
        self._our_robot = self._world.our_attacker

        self._robot_controller = robot_controller

        # Strategy dictionaries return a strategy given a state.
        if self._profile == 'attacker':  # MS2+
            self._strategies = {
                NO_BALL: Idle(self._world, self._robot_controller),
                BALL_OUR_A_ZONE: GetBall(self._world, self._robot_controller),
                BALL_OUR_D_ZONE: CatchBall(self._world, self._robot_controller),
                BALL_THEIR_A_ZONE: Confuse(self._world, self._robot_controller),
                BALL_THEIR_D_ZONE: Intercept(self._world, self._robot_controller),
                POSSESSION: PassBall(self._world, self._robot_controller)
            }

        # Choose initial strategy
        self._state = NO_BALL
        self._strategy = None
        self.update_strategy()

    def plan(self):
        """
        Update planner state before commanding the robot.
        """
        self.attacker_transition()
        self._strategy.transition()

        print self._state
        
        # Get action from strategy then call if not None
        plan = self._strategy.get_action()
        if plan is not None:
            plan()

    def update_strategy(self):
        """
        Set the appropriate strategy given the current state.
        If you wish to switch to a 'fresh' copy of the current
        strategy then you must explicitly call its reset method.
        """
        new_strategy = self._strategies[self._state]
        if new_strategy is not self._strategy:

            if self._strategy is not None:
                self._strategy.reset()  
                
        self._strategy = new_strategy

    def attacker_transition(self):
        """
        Update the planner state and strategy given the current state of the
        world model.

        For the attacker profile.
        """
        # For mil3: make this the get ball + pass logic

        # If the ball is not in play
        if not self._world.ball_in_play():
            self._state = NO_BALL

        # If ball is in play but not in our margin
        elif self._world.ball_in_area([self._world.our_defender]):
            self._state = BALL_OUR_D_ZONE
        elif self._world.ball_in_area([self._world.their_attacker]):
            self._state = BALL_THEIR_A_ZONE
        elif self._world.ball_in_area([self._world.their_defender]):
            self._state = BALL_THEIR_D_ZONE

        # If ball is in our margin
        elif self._world.ball_in_area([self._our_robot]):

            # Check for strategy final state
            if self._strategy.final_state():

                # Successfully grabbed ball
                if isinstance(self._strategy, GetBall):
                    self._state = POSSESSION

                # Had ball and have kicked
                elif isinstance(self._strategy, PassBall):
                    self._state = BALL_OUR_A_ZONE
                    pass

        self.update_strategy()
