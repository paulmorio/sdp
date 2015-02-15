from tools import *


# Top-level state constants
NO_BALL = 'no_ball'  # Ball not yet seen, not in play areas (init state)
BALL_UNREACHABLE = 'ball_unreachable'  # Ball not in our margin
BALL_REACHABLE = 'ball_reachable'  # Ball in our margin
POSSESSION = 'have_possession'  # Our robot has the ball in its grabber


class Planner:

    def __init__(self, world, robot_controller, profile):
        """
        Create a planner object.
        :param world: World model object from pc.models.worldmodel.
        :param robot_controller: Robot control object from pc.robot
        :param profile: Planning profile.
        """
        self.world = world
        self.robot_controller = robot_controller

        assert (profile in ['attacker', 'passer'])
        self.profile = profile

        # Transition dictionaries return a strategy given a state.
        if self.profile == 'attacker':  # MS2+
            self.transitions = {
                NO_BALL: Idle(self.world),
                BALL_UNREACHABLE: Intercept(self.world),
                BALL_REACHABLE: GetBall(self.world),
                POSSESSION: ShootBall(self.world)
            }
            self.state = NO_BALL
        elif self.profile == 'passer':  # MS3
            self.transitions = {
                NO_BALL: Idle(self.world),
                BALL_UNREACHABLE: Intercept(self.world),
                BALL_REACHABLE: GetBall(self.world),
                POSSESSION: PassBall(self.world)
            }
        # Choose initial strategy
        self.state = NO_BALL
        self.strategy = self.transition()

    def transition(self):
        """
        Transition to the appropriate strategy state given the current
        strategy and top-level state.
        :return: Strategy object
        """
        if self.strategy is not None:
            # Reset the state of the strategy before transitioning
            self.strategy.reset()
        return self.transitions[self.state]

    def update_plan(self):
        """
        Run the appropriate planner for the given profile.
        """
        plan = None
        if self.profile == 'attacker':
            plan = self.attacker_plan()
        elif self.profile == 'passer':
            plan = self.passer_plan()
        if plan is not None:
            pass
            # TODO send plan/action to robot controller

    def attacker_plan(self):
        """
        Determine new strategy given the current world state. MS2
        :return: Plan/action for robot.
        """
        # Get relevant world objects
        our_attacker = self.world.our_attacker

        # If the ball is not in play
        if not self.world.ball_in_play():
            if self.state != NO_BALL:
                self.state = NO_BALL
                self.transition()
            return self.strategy.get_plan()

        # If ball is in play but unreachable (outwith our margin)
        elif not self.world.ball_in_area([our_attacker]):
            if not self.state == BALL_UNREACHABLE:
                self.state = BALL_UNREACHABLE
                self.transition()
            return self.strategy.get_plan()

        # If ball is in our margin
        elif self.world.ball_in_area([our_attacker]):

            # Chasing ball and successfully grabbed
            if self.state == BALL_REACHABLE and self.strategy.state == GRABBED:
                self.state = POSSESSION
                self.transition()

            # Had ball and have kicked
            elif self.state == POSSESSION and self.strategy.state == KICKED:
                self.state = BALL_REACHABLE
                self.transition()

            # Ball has just become reachable
            elif self.state == BALL_UNREACHABLE or self.state == NO_BALL:
                self.state = BALL_REACHABLE
                self.transition()

            return self.strategy.get_plan()

    def passer_plan(self):
        pass