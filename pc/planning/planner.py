from strategies import *
from utilities import *


class Planner:

    def __init__(self, world, robot_controller, role):
        self.world = world
        self.robot_controller = robot_controller
        self.role = role
        assert (role in ['attacker', 'defender'])

        # Set up strategies - given a state (key) return a strategy (val)
        if role == 'attacker':
            self.strategies = {
                'ball_in_margin': AttackerGetBall,
                'grab': AttackerGrabBall,
                'possession': AttackerShoot,
                'defend': AttackerInterceptBall
            }
            self.state = 'ball_in_margin'
        else:
            self.strategies = {
                'init': DefenderWaitForMovement,
                'defend': DefenderInterceptBall,
                'ball_in_margin': DefenderGetBall,
                'grab': DefenderGrabBall,
                'possession': DefenderPassBall
            }
            self.state = 'init'

        self.strategy = self.choose_strategy()

    # Provisional. Choose the first strategy in the applicable list.
    def choose_strategy(self):
        next_strategy = self.strategies[self.state]
        return next_strategy(self.world)

    def plan(self):
        if self.role == 'defender':
            self.defender_plan()
        else:
            self.attacker_plan()

    def defender_plan(self):
        our_defender = self.world.our_defender
        ball = self.world.ball

        # If the ball is in their attacker zone:
        if not self.world.pitch.zones[our_defender.zone].isInside(ball.x,
                                                                  ball.y):
            # If the ball is not in the defender's zone,
            # the state should always be 'defend'.
            if not self.state == 'defend':
                self.state = 'defend'
                self.strategy = self.choose_strategy()
            return self.strategy.generate()

        # We have the ball in our zone, so we grab and pass:
        elif self.world.pitch.zones[our_defender.zone].isInside(ball.x, ball.y):
            # Check if we should switch from a grabbing to a passing strategy.
            if self.state == 'grab' and \
                    self.strategy.current_state == 'GRABBED':
                self.state = 'possession'
                self.strategy = self.choose_strategy()

            # Check if we should switch from a defence to a chasing strategy.
            elif self.state == 'defend':
                self.state = 'ball_in_margin'
                self.strategy = self.choose_strategy()

            # If ball in grabber area, switch to grab strategy
            elif self.state == 'ball_in_margin':  # TODO and in grabber area
                self.state = 'grab'
                self.strategy = self.choose_strategy()

            # If we have passed the ball, switch back to chase strategy
            elif self.state == 'possession' \
                    and self.strategy.current_state == 'PASSED':
                self.state = 'ball_in_margin'
                self.strategy = self.choose_strategy()
            return self.strategy.generate()
        else:
            return do_nothing()

    def attacker_plan(self):
        our_attacker = self.world.our_attacker
        their_defender = self.world.their_defender
        ball = self.world.ball

        # If ball is in our attacker zone, then grab the ball and score:
        if self.world.pitch.zones[our_attacker.zone].isInside(ball.x, ball.y):
            # Switch to scoring strategy
            if self.state == 'grab' \
                    and self.strategy.current_state == 'GRABBED':
                self.state = 'possession'
                self.strategy = self.choose_strategy()

            # Switch to grabbing strategy
            elif self.state == 'ball_in_margin':  # TODO and ball in grabber zone
                self.state = 'grab'
                self.strategy = self.choose_strategy()

            # Switch to chase strategy if we've shot the ball
            elif self.state == 'possession':  # TODO and have shot ball
                self.state = 'ball_in_margin'
                self.strategy = self.choose_strategy()

            # If ball has returned to margin after defense
            elif self.state == 'defend':
                self.state = 'ball_in_margin'
                self.strategy = self.choose_strategy()
            return self.strategy.generate()

        # If ball in their defender zone, switch to intercept tactic
        elif self.world.pitch.zones[their_defender.zone].isInside(ball.x,
                                                                  ball.y):
            if self.state != 'defend':
                self.state = 'defend'
                self.choose_strategy()
            return self.strategy.generate()
        else:
            return do_nothing()