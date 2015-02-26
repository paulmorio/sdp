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
        assert (profile in ['passer', 'receiver'])
        self._world = world
        self._profile = profile
        self._our_robot = self._world.our_attacker

        self._robot_controller = robot_controller

        # Strategy dictionaries return a strategy given a state.
        if self._profile == 'passer':  # MS2+
            self._strategies = {
                NO_BALL: Idle(self._world, self._robot_controller),
                BALL_OUR_A_ZONE: GetBall(self._world, self._robot_controller),
                BALL_OUR_D_ZONE: CatchBall(self._world, self._robot_controller),
                BALL_THEIR_A_ZONE: Confuse(self._world, self._robot_controller),
                BALL_THEIR_D_ZONE: Intercept(self._world, self._robot_controller),
                POSSESSION: PassBall(self._world, self._robot_controller)
            }
        elif self._profile == 'receiver':  # MS3
            self._strategies = {
                NO_BALL: Idle(self._world, self._robot_controller),
                BALL_OUR_A_ZONE: GetBall(self._world, self._robot_controller),
                BALL_OUR_D_ZONE: CatchBall(self._world, self._robot_controller),
                BALL_THEIR_A_ZONE: CatchBall(self._world, self._robot_controller),
                BALL_THEIR_D_ZONE: CatchBall(self._world, self._robot_controller),
                POSSESSION: Sleep(self._world, self._robot_controller)
            }
        # Choose initial strategy
        self._state = NO_BALL
        self._strategy = None
        self.update_strategy()

    def plan(self):
        """
        Update planner state before commanding the robot.
        """
        # Run the appropriate transition function
        if self._profile == 'passer':
            self.passer_transition()
        elif self._profile == 'receiver':
            self.receiver_transition()

        self._strategy.transition()  # Update strategy state

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
        # If new strategy is not the same as the old.
        new_strategy = self._strategies[self._state]
        if new_strategy is not self._strategy:
            if self._strategy is not None:
                self._strategy.reset()
            self._strategy = new_strategy

    def passer_transition(self):
        """
        Update the planner state and strategy given the current state of the
        world model.

        For the passer profile.
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

            # Ball has just become reachable
            if self._our_robot.can_catch_ball(self._world.ball):
                self._state = POSSESSION
            elif self._state == BALL_OUR_D_ZONE or self._state == BALL_THEIR_A_ZONE or \
                    self._state == BALL_THEIR_D_ZONE or self._state == NO_BALL:
                self._state = BALL_OUR_A_ZONE

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

    def receiver_transition(self):
        """
        For the receiver profile.
        Update the planner state and strategy given the current state of the
        world model.
        """
        # For mil3: make this the pass accepting + get ball logic

        print self._state

        # If the ball is not in play
        if not self._world.ball_in_play():
            self._state = NO_BALL

        # If ball is in our margin
        elif self._world.ball_in_area([self._our_robot]):

            # Ball has just become reachable
            if self._state == BALL_OUR_D_ZONE or self._state == BALL_THEIR_A_ZONE or \
                    self._state == BALL_THEIR_D_ZONE or self._state == NO_BALL:
                self._state = BALL_OUR_A_ZONE

            # Check for strategy final state
            if self._strategy.final_state():
                # Catch/intercept ball
                if isinstance(self._strategy, CatchBall):
                    # Caught the ball - now prepare to get possession of it
                    self._state = BALL_OUR_A_ZONE

                # Get the ball
                elif isinstance(self._strategy, GetBall):
                    # Got possession of the ball - now prepare to sleep
                    self._state = POSSESSION

                # Have the ball, now sleep
                elif isinstance(self._strategy, Sleep):
                    pass

        # If ball is in play but unreachable (outwith our margin)
        elif self._world.ball_in_area([self._world.our_defender]):
            self._state = BALL_OUR_D_ZONE
        elif self._world.ball_in_area([self._world.their_attacker]):
            self._state = BALL_THEIR_A_ZONE
        elif self._world.ball_in_area([self._world.their_defender]):
            self._state = BALL_THEIR_D_ZONE

        self.update_strategy()
