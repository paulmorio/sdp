from strategies import *
from utilities import *


class Planner(object):

    def __init__(self, world, robot_controller, profile):
        """
        Create a planner object.
        :param world: World model object from pc.models.worldmodel.
        :param robot_controller: Robot control object from pc.robot
        :param profile: Planning profile.
        """
        self._world = world
        assert (profile in ['attacker', 'receiver'])
        self._profile = profile
        if profile == "attacker":
            self._our_robot = self._world.our_attacker
        elif profile == "receiver":
            self._our_robot = self._world.our_defender
        self._robot_controller = robot_controller

        # Strategy dictionaries return a strategy given a state.
        if self._profile == 'attacker':  # MS2+
            self._strategies = {
                NO_BALL: Idle(self._world, self._robot_controller),
                BALL_OURATTACKER: GetBall(self._world, self._robot_controller),
                BALL_OURDEFENDER: CatchBall(self._world, self._robot_controller),
                BALL_THEIRATTACKER: Confuse(self._world, self._robot_controller),
                BALL_THEIRDEFENDER: Intercept(self._world, self._robot_controller),
                POSSESSION: PassBall(self._world, self._robot_controller)
            }
        elif self._profile == 'receiver':  # MS3
            self._strategies = {
                NO_BALL: Idle(self._world, self._robot_controller),
                BALL_OURATTACKER: CatchBall(self._world, self._robot_controller),
                BALL_OURDEFENDER: GetBall(self._world, self._robot_controller),
                BALL_THEIRATTACKER: CatchBall(self._world, self._robot_controller),
                BALL_THEIRDEFENDER: CatchBall(self._world, self._robot_controller),
                POSSESSION: Idle(self._world, self._robot_controller)
            }
        # Choose initial strategy
        self._state = NO_BALL
        self._strategy = None
        self.update_strategy()

    def plan(self):
        """Update planner state before commanding the robot."""
        # Run the appropriate transition function
        if self._profile == 'attacker':
            self.attacker_transition()
        elif self._profile == 'receiver':
            self.receiver_transition()

        self._strategy.transition()  # Update strategy state

        plan = self._strategy.get_action()
        if plan is not None:
            plan()
            # TODO send plan/action to robot controller

    def update_strategy(self):
        """
        Set the appropriate strategy given the current state.
        If you wish to switch to a 'fresh' copy of the current
        strategy then you must explicitly call its reset method.
        """
        # If new strategy is actually new.
        new_strategy = self._strategies[self._state]
        if new_strategy is not self._strategy:
            if self._strategy is not None:
                self._strategy.reset()
            self._strategy = new_strategy

    def attacker_transition(self):
        """
        For the attacker profile.
        Update the planner state and strategy given the current state of the
        world model.
        """
        # For mil3: make this the get ball + pass logic

        print self._state

        # If the ball is not in play
        if not self._world.ball_in_play():
            self._state = NO_BALL

        # If ball is in our margin
        elif self._world.ball_in_area([self._our_robot]):

            # Ball has just become reachable
            if self._state == BALL_OURDEFENDER or self._state == BALL_THEIRATTACKER or self._state == BALL_THEIRDEFENDER or self._state == NO_BALL:
                self._state = BALL_OURATTACKER

            # Check for strategy final state
            if self._strategy.final_state():
                if isinstance(self._strategy, GetBall):
                    self._state = POSSESSION

                # Had ball and have kicked
                elif isinstance(self._strategy, PassBall):
                    self._state = BALL_OURATTACKER
                    pass

        # If ball is in play but unreachable (outwith our margin)
        elif self._world.ball_in_area([self._world.our_defender]):
            self._state = BALL_OURDEFENDER
        elif self._world.ball_in_area([self._world.their_attacker]):
            self._state = BALL_THEIRATTACKER
        elif self._world.ball_in_area([self._world.their_defender]):
            self._state = BALL_THEIRDEFENDER

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
            if self._state == BALL_OURATTACKER or self._state == BALL_THEIRATTACKER or self._state == BALL_THEIRDEFENDER or self._state == NO_BALL:
                self._state = BALL_OURDEFENDER

            # Check for strategy final state
            if self._strategy.final_state():
                # Catch/intercept ball
                if isinstance(self._strategy, CatchBall):
                    # Caught the ball - now prepare to get possession of it
                    self._state = BALL_OURDEFENDER

                # Get the ball
                elif isinstance(self._strategy, GetBall):
                    # Got possession of the ball - now prepare to idle
                    self._state = POSSESSION

                # Have the ball, now idle
                elif isinstance(self._strategy, Idle):
                    pass

        # If ball is in play but unreachable (outwith our margin)
        elif self._world.ball_in_area([self._world.our_attacker]):
            self._state = BALL_OURATTACKER
        elif self._world.ball_in_area([self._world.their_attacker]):
            self._state = BALL_THEIRATTACKER
        elif self._world.ball_in_area([self._world.their_defender]):
            self._state = BALL_THEIRDEFENDER

        self.update_strategy()
