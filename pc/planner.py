from models.worldmodel import *
from robot import Robot


# Methods that 

class Planner():

    # MILESTONE
    def __init__(self, world, robotController, mode):
        self.world = world
        self.mode = mode
        self.state = None  # refactor planner into strategies at some point - not important for this milestone

        # action the robot is currently executing:
        self.action = "idle"
        # none
        # turn-left
        # turn-right
        # move-forward
        # crawl-forward <- TODO: add crawl-forward command in robot.py for arduino: move forward at LOW ACCURATE speed
        ## move-backward
        ## strafe-left
        ## strafe-right
        ## grabbing
        ## releasing
        ## kicking
        

        # Our controllable robot (ie. NOT OBSERVED, but ACTUAL arduino one)
        self.robotController = robotController

        # bot we are making plans for, OBSERVED robot via the vision.
        if (self.mode == 'attacker'):
            self.bot = self.world.our_attacker()
        elif(self.mode == 'defender'):
            self.bot = self.world.our_defender()
        elif(self.mode == 'dog'):
            self.bot = self.world.our_attacker
        else:
            print "Not recognized mode!"

    ################################
    ########## SUBPLANS ############
    ################################

    def inside_grabber(self):
        ball = self.world.ball
        return self.bot.can_catch_ball(ball)

    def get_direction_to_rotate(self, pitch_object):
        """
        Returns a string indicating which direction to turn clockwise/a-clockwise depending on angle
        """
        angle = self.bot.get_rotation_to_point(pitch_object.x, pitch_object.y)

        if angle <= 0:  # If the angle is greater than bearing + ~6 degrees, rotate CLKW (towards origin)
            return 'turn-right'
        elif angle > 0:  # If the angle is less than bearing - ~6 degrees, rotate ACLKW (away from origin)
            return 'turn-left'
        else:
            return 'none'

    # This method is likely unnecessary but kept because it is used in teuns dog implementation.
    def bot_rotate_to_direction(self, direction):
        """
        Rotates bot towards given direction

        needs more clarification on how much to turn etc based on refresh of world
        or on some time factor, or some amount to turn.
        """
        if direction == 'turn-right':
            self.robotController.command(Robot.TURN_RIGHT)
        elif direction == 'turn-left':
            self.robotController.command(Robot.TURN_LEFT)
        elif direction == 'none':
            self.robotController.command(Robot.STOP_MOTORS)
        else:
            print "ERROR in get_direction_to_rotate"

    # Issue11
    def bot_rotate_or_move(self, direction):
        """
        Rotates bot towards given direction, or moves forward if the direction is none
        """
        if direction == 'turn-right':
            self.robotController.command(Robot.TURN_RIGHT)
        elif direction == 'turn-left':
            self.robotController.command(Robot.TURN_LEFT)
        else:
            print "ERROR in get_direction_to_rotate"

    # Issue11
    def bot_get_ball(self):
        """
        Has the bot move to the ball, and grab it
        """
        ball = self.world._ball

        # We have to make sure we don't have the ball already
        if not self.bot.has_ball:
                    # If the robot cannot catch the ball yet
            if not self.bot.can_catch_ball(ball):
                dir_to_rotate = self.get_direction_to_rotate(ball)
                #self.bot_rotate_and_go(dir_to_rotate)

            # Otherwise (if the ball is within catching range) "grab" until we have possession of the ball
            else:
                self.robotController.command(Robot.GRAB)

        else:
            pass

    # Issue11
    def rotate_towards_goal_and_shoot(self):
        """
        when the bot has possession of the ball, will cause it to rotate to their goal and shoot
        """
        # Now that we have the ball, rotate towards the own goal.
        dir_to_rotate = self.get_direction_to_rotate(self.world.their_goal)
        if dir_to_rotate != 'none':
            pass    #self.bot_rotate(dir_to_rotate)
        else:  # Finished rotating to face goal, can now kick
            self.robotController.command(Robot.KICK)

    # MILESTONE
    def bot_pass_forward(self):
        """
        When the bot has possession of the ball, will cause it to rotate towards their goal and pass
        """
        # Now that we have the ball, rotate towards the right attacking zone.  # IMPORTANT: 'side' has to be 'left'
        dir_to_rotate = self.get_direction_to_rotate(self.world.their_goal)
        if dir_to_rotate != 'none':  # If we need to rotate, do so
            pass    #self.bot_rotate(dir_to_rotate)
        else:  # Finished rotating to face goal, can now kick
            self.bot.command(self.bot.PASS)  # TODO: pass? Can just replace with a "KICK" depending.

    # ISSUE11
    def bot_shadow_target(self):
        """
        Simple defensive solution when the ball is not in our defending zone, rotate to move on the y-axis only, 
        and attempt to shadow the ball along the y axis
        """
        ball = self.world.ball

        # If the ball is not in our zone, stay mobile
        if not self.world.pitch.zones[self.world.our_defender.zone].isInside(ball.x, ball.y):
            # face ~3/2pi angle, ie towards the bottom of the pitch
            angle = self.bot.angle
            desired = (3.0 / 2.0) * pi

            if angle < desired - 0.1:
                self.robotController.command(Robot.TURN_LEFT)
            elif angle > desired + 0.1:
                self.robotController.command(Robot.TURN_RIGHT)

            # if the balls ~y co-ord is bigger than ours, move forwards to intercept
            # if the balls ~y co-rds is less than ours, move backwards to intercept
            if ball.y > self.bot.y + 5:
                self.robotController.command(Robot.MOVE_FORWARD)
            elif ball.y < self.bot.y - 5:
                self.robotController.command(Robot.MOVE_BACK)

    def aiming_towards_object(self, instance):
        # returns true if bot direction is towards instance
        if abs(self.bot.get_rotation_to_point(instance.x, instance.y)) > 0.1:
            return False
        else:
            return True

    #################################
    ########## AGGREGATORS ##########
    #################################

    def determine_state(self, mode):
        """
        This method determines the state of the robot given the robots mode, 
        and the situation on the pitch

        :param mode: anything from ['dog', 'attacker', 'defender']
        """

        # for our dear toy example, he never has the ball
        if self.mode == 'dog':
            return 'noBall'

        if self.mode == 'attacker':

            ball_x = self.world._ball.x()
            ball_y = self.world._ball.y()

            if (self.world._pitch.is_within_bounds(self.bot, ball_x, ball_y)):
                return 'inZoneNoBall'

            if (self.bot.has_ball(self.world._ball)):
                return 'hasBall'

            if (self.world.their_defender().has_ball(self.world._ball)):
                return 'opponentDefenderHasBall'

            if (self.world.our_defender().has_ball(self.world._ball)):
                return 'ourDefenderHasBall'

        if self.mode == 'defender':

            ball_x = self.world.ball.x
            ball_y = self.world.ball.y

            # The ball is in our defender's zone
            if self.world.pitch.is_within_bounds(self.bot, ball_x, ball_y):
                return 'inZone'

            # The ball is in our attacker's zone
            if self.world.pitch.is_within_bounds(self.world.our_attacker, ball_x, ball_y):
                return 'inOurAttackerZone'

            # etc..
            if self.world.pitch.is_within_bounds(self.world.their_defender, ball_x, ball_y):
                return 'inTheirDefenderZone'

            if self.world.pitch.is_within_bounds(self.world.their_attackerr, ball_x, ball_y):
                return 'inTheirAttackerZone'


            # Our defender has possession
            if self.bot.has_ball(self.world.ball):
                return 'hasBall'

            # Our attacker has the ball
            if self.world.our_attacker().has_ball(self.world.ball):
                return 'ourAttackerHasBall'

            # etc..
            if self.world.their_defender().has_ball(self.world.ball):
                return 'opponentDefenderHasBall'

            if self.world.their_attacker().has_ball(self.world.ball):
                return 'opponentAttackerHasBall'

    # UPDATED "TICK" function 
    def updatePlan(self):
        """
        Makes plans based on the mode of the planner, and the state determined
        by the current situation (which can be found through determine_state)
        """

        # find out situation of robot (mode)
        self.state = self.determine_state(self.mode)

        # Find the different situations (states) the attacker can be in
        if self.mode == 'attacker':

            # State when the ball is in the robots own zone but doesnt have the ball
            # Go to ball and move to a better location.
            if (self.state == 'inZoneNoBall'):
                ball_x = self.world._ball.x()
                ball_y = self.world._ball.y()

                angle_to_turn_to = self.bot.get_rotation_to_point(ball_x,ball_y)
                distance_to_move = self.bot.get_displacement_to_point(ball_x, ball_y)

                dir_to_turn = get_direction_to_rotate(self.world._ball)

                # We command the robot turn to the ball, and move forward if it is facing it.
                # This is implementation is deeply simplified (but works)
                bot_rotate_or_move(dir_to_turn)

            # State when the ball is in possession by the robot, time to align with goal
            # and shoot.
            elif (self.state == 'hasBall'):
                rotate_towards_goal_and_shoot()

            # State when the ball is in possession of the opponents defender
            # Time to shadow the opponent defender.
            elif (self.state == 'opponentDefenderHasBall'):
                defen_x = self.world.their_defender()._x
                defen_y = self.world.their_defender()._y

                #idea is to keep aligned with them along one axis and shadow movement
                bot_shadow_target()

            # State where the ball in possession of our defender
            # Time to shadow our defender so that ball comes to our possession.
            elif (self.state == 'ourDefenderHasBall'):
                defen_x = self.world.our_defender()._x
                defen_y = self.world.our_defender()._y

                #idea is to keep aligned with them along one axis and shadow movement
                #bot_shadow_target()
            else:
                pass
                #bot_shadow_target()

        # Find the different situations (states) the defender can be in
        elif self.mode == 'defender':
            # Basic idea: Intercept ball>collect ball>pass forward
            state = self.state

            if (self.state == 'noBall'):
                if (not ball_is_owned()):
                    if (not is_grabber_opened):
                        open_grabbers()
                    self.robotController.move_vertical(pitch_get_height()/2)
                else:
                    if (not ball_is_idle()):
                        self.robotController.move_vertical(ball._y)
                        if (not aiming_towards_object(ball)):
                             self.robotController.rotate_towards_point(ball._x,ball._y)
                        distance_to_ball = self.bot.get_displacement_to_point(ball._x,ball._y)
                        if (distance_to_ball == 0): # TODO update 0 into variable depending on future: ball velocity, attempt to close grabbers exaclty at the time the ball rolls into grabbers
                            if (is_grabber_opened()):
                                self.robotController.close_grabbers()
                            self.state = 'hasBall'
                    else:
                        self.mode = 'dog' # FETCH!! (WARNING: doggie style does not care about our field in the pitch)
            """
            # Awaiting future refactorings
            if state == 'inZone':
                if state == 'hasBall':
                    pass_forward()
                else:
                    fetch_ball()
            if state == 'inOurAttackerZone':
                defender_idle()
            if state == 'inTheirDefenderZone':
                defender_idle()
            if state == 'inTheirAttackerZone':
                defender_mark_attacker()



            if state == 'ourAttackerHasBall':
                defender_idle()
            if state == 'opponentDefenderHasBall':
                defender_idle()
            if state == 'opponentAttackerHasBall':
                defender_block()
            """

        # Dog Mode for robot. NB: This is hacked together it would be better to move this into seperate functions
        elif (self.mode == 'dog'):

            # If the robot does not have the ball, it should go to the ball.
            if (self.state == 'noBall'):
                # Get the ball position so that we may find the angle to align with it, as well as the displacement
                ball_x = self.world._ball.x
                ball_y = self.world._ball.y
                rotate_margin = 0.75
                inside_grabber = self.inside_grabber()

                angle_to_turn_to = self.bot.get_rotation_to_point(ball_x,ball_y)
                distance_to_move = self.bot.get_displacement_to_point(ball_x, ball_y)

                dir_to_turn = self.get_direction_to_rotate(self.world._ball)

                # IF NOT FACING BALL
                if (abs(angle_to_turn_to) > rotate_margin):

                    # [ACTIVE] IF NOT ALREADY TURNING
                    if (self.action != "turn-right" and self.action != "turn-left"):
                        self.bot_rotate_to_direction(dir_to_turn)
                        self.action = dir_to_turn

                        if (dir_to_turn == "turn-left"):
                            print "ROTATE: <<<"
                        elif (dir_to_turn == "turn-right"):
                            print "ROTATE: >>>"
                        else:
                            print "Facing Ball - ball slightly on : "+dir_to_turn+" side"

                    # [PASSIVE] IF ALREADY TURNING
                    else:
                        pass
                        #print self.action+" is still executing, angle to ball: "+str(angle_to_turn_to)

                # IF FACING BALL
                else:

                    # [ACTIVE] IF STILL TURNING
                    if (self.action == "turn-right" or self.action == "turn-left"):
                        self.action = "idle"
                        self.robotController.command(Robot.STOP_MOTORS)

                        print "ROTATE: _ _ _"

                    # [ACTIVE] IF IDLE && OUTSIDE OF GRAB-RANGE
                    if (self.action == "idle" and not inside_grabber):
                        self.action = "move-forward"
                        self.robotController.command(Robot.MOVE_FORWARD)

                        print "MOVE: ^^^"

                    # [PASSIVE] IF ALREADY MOVING FORWARD && OUTSIDE OF GRAB-RANGE
                    elif (self.action == "move-forward" and not inside_grabber):
                        pass
                        #print "Still moving forward"
                        #print "Distance to ball: "+str(distance_to_move)

                    # [ACTIVE] IF MOVING FORWARD BUT INSIDE GRAB RANGE
                    elif (self.action == "move-forward" and inside_grabber):
                        self.robotController.command(Robot.STOP_MOTORS)
                        self.action = "idle"
                        print "MOVE: _ _ _"

                    # [PASSIVE] IF IDLE && INSIDE GRAB-RANGE
                    elif (self.action == "idle" and inside_grabber):
                        pass
                        #print "Suntanning :)"

            else:
                print "Error, cannot find mode"