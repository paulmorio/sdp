from models.worldmodel import *
from robot import *
from time import sleep


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
        self.robotStarted=40 # init robot actions

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

    def ball_inside_zone(self):
        ball = self.world.ball
        return self.world.pitch.is_within_bounds(self.bot, ball.x, ball.y)

    def robot_inside_zone(self):
        print "("+str(self.bot.x)+","+str(self.bot.y)+")"
        print str(self.world.pitch.zones[self.bot.zone].isInside(self.bot.x, self.bot.y))
        return True

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
            self.robotController.command(TURN_RIGHT)
        elif direction == 'turn-left':
            self.robotController.command(TURN_LEFT)
        elif direction == 'none':
            self.robotController.command(STOP_DRIVE_MOTORS)
        else:
            print "ERROR in get_direction_to_rotate"

    def bot_look_at(self, pitch_object, rotate_margin):

        angle_to_turn_to = self.bot.get_rotation_to_point(pitch_object.x, pitch_object.y)

        dir_to_turn = self.get_direction_to_rotate(pitch_object)

        # IF NOT FACING OBJECT
        if abs(angle_to_turn_to) > rotate_margin:

            # [ACTIVE] IF NOT ALREADY TURNING
            if self.action != "turn-right" and self.action != "turn-left":
                self.bot_rotate_to_direction(dir_to_turn)
                self.action = dir_to_turn

                if dir_to_turn == "turn-left":
                    print "ROTATE: <<<"
                elif dir_to_turn == "turn-right":
                    print "ROTATE: >>>"
                else:
                    print "Facing object - object slightly on : "+dir_to_turn+" side"

            # [PASSIVE] IF ALREADY TURNING
            else:
                # [ACTIVE] IF TURNING BUT BALL CHANGED DIRECTION
                pass

        # IF FACING OBJECT
        else:

            # [ACTIVE] IF STILL TURNING
            if self.action == "turn-right" or self.action == "turn-left":
                self.bot_stop()

    # Issue11
    def bot_rotate_or_move(self, direction):
        """
        Rotates bot towards given direction, or moves forward if the direction is none
        """
        if direction == 'turn-right':
            self.robotController.command(TURN_RIGHT)
        elif direction == 'turn-left':
            self.robotController.command(TURN_LEFT)
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
                self.robotController.command(GRABBER_OPEN)

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
            self.robotController.command(SHOOT)

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
            self.bot.command(PASS)  # TODO: pass? Can just replace with a "KICK" depending.

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
                self.robotController.command(TURN_LEFT)
            elif angle > desired + 0.1:
                self.robotController.command(TURN_RIGHT)

            # if the balls ~y co-ord is bigger than ours, move forwards to intercept
            # if the balls ~y co-rds is less than ours, move backwards to intercept
            if ball.y > self.bot.y + 5:
                self.robotController.command(MOVE_FORWARD)
            elif ball.y < self.bot.y - 5:
                self.robotController.command(MOVE_BACK)

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

    def bot_stop(self):
        self.robotController.command(STOP_DRIVE_MOTORS)
        self.action = "idle"
        print "MOVE: _ _ _"

    def bot_open_grabber(self):
        self.robotController.command(GRABBER_OPEN)
        self.bot.catcher = "open"
        print "GRABBER: OPEN"

    def bot_close_grabber(self):
        self.robotController.command(GRABBER_CLOSE)
        self.bot.catcher = "closed"
        print "GRABBER: CLOSE"

    # UPDATED "TICK" function 
    def updatePlan(self):
        """
        Makes plans based on the mode of the planner, and the state determined
        by the current situation (which can be found through determine_state)
        """
        if (self.robotStarted > 0):
            self.robotStarted -= 1
            print "NUKE IN .."+str(self.robotStarted)
        else:
            # find out situation of robot (mode)
            self.state = self.determine_state(self.mode)
            ball = self.world.ball
            #print str(self.robot_inside_zone())

            # Find the different situations (states) the attacker can be in
            if self.mode == 'attacker':

                # State when the ball is in the robots own zone but doesnt have the ball
                # Go to ball and move to a better location.
                if (self.state == 'inZoneNoBall'):
                    ball_x = self.world._ball.x()
                    ball_y = self.world._ball.y()

                    angle_to_turn_to = self.bot.get_rotation_to_point(ball_x,ball_y)
                    distance_to_move = self.bot.get_displacement_to_point(ball_x, ball_y)

                    dir_to_turn = self.get_direction_to_rotate(self.world._ball)

                    # We command the robot turn to the ball, and move forward if it is facing it.
                    # This is implementation is deeply simplified (but works)
                    self.bot_rotate_or_move(dir_to_turn)

                # State when the ball is in possession by the robot, time to align with goal
                # and shoot.
                elif (self.state == 'hasBall'):
                    self.rotate_towards_goal_and_shoot()

                # State when the ball is in possession of the opponents defender
                # Time to shadow the opponent defender.
                elif (self.state == 'opponentDefenderHasBall'):
                    defen_x = self.world.their_defender()._x
                    defen_y = self.world.their_defender()._y

                    #idea is to keep aligned with them along one axis and shadow movement
                    self.bot_shadow_target()

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
                # TODO:
                # Awaiting future refactorings
                if state == 'inZone':
                    if state == 'hasBall':
                        self.pass_forward()
                    else:
                        self.fetch_ball()
                if state == 'inOurAttackerZone':
                    self.defender_idle()
                if state == 'inTheirDefenderZone':
                    self.defender_idle()
                if state == 'inTheirAttackerZone':
                    self.defender_mark_attacker()

                if state == 'ourAttackerHasBall':
                    self.defender_idle()
                if state == 'opponentDefenderHasBall':
                    self.defender_idle()
                if state == 'opponentAttackerHasBall':
                    self.defender_block()


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
                            # [ACTIVE] IF TURNING BUT BALL CHANGED DIRECTION
                            pass

                    # IF FACING BALL
                    else:

                        # [ACTIVE] IF STILL TURNING
                        if (self.action == "turn-right" or self.action == "turn-left"):
                            self.bot_stop()

                        # [ACTIVE] IF IDLE && OUTSIDE OF GRAB-RANGE && BALL INSIDE ZONE
                        elif (self.action == "idle" and not inside_grabber and self.ball_inside_zone()):
                            self.action = "move-forward"
                            self.robotController.command(MOVE_FORWARD)

                            print "MOVE: ^^^"

                        # IF ALREADY MOVING FORWARD && OUTSIDE OF GRAB-RANGE
                        elif (self.action == "move-forward" and not inside_grabber):

                            # [ACTIVE] IF BALL ROLLS OUT OF ZONE WHILE CHASING
                            if (not self.ball_inside_zone()):
                                self.bot_stop()

                            # [PASSIVE] BALL IN ZONE
                            else:
                                pass

                        # [ACTIVE] IF MOVING FORWARD BUT INSIDE GRAB RANGE
                        elif (self.action == "move-forward" and inside_grabber):
                            print "IN GRABBER RANGE"
                            self.bot_stop()

                        # [PASSIVE] IF IDLE && INSIDE GRAB-RANGE
                        elif (self.action == "idle" and inside_grabber):
                            print "KICK"
                            self.robotController.command(KICK)
                            #print "Suntanning :)"

                    # [PASSIVE] IF BALL OUTSIDE ZONE
                    if (not self.ball_inside_zone()):
                        #print "Ball out of reach T.T "
                        pass

                else:
                    print "Error, cannot find mode"

    def pass_forward(self):
        """
        -rotate to face our attacker
        -open grabber, pass ball
        # assumes there's no obstacles in the way, for the moment
        """

        # TODO: code stolen from above - re-steal when updated work is committed
        rotate_margin = 0.75
        our_attacker = self.world.our_attacker
        angle_to_turn_to = self.bot.get_rotation_to_point(our_attacker.x, our_attacker.y)
        dir_to_turn = self.get_direction_to_rotate(self.world.ball)

        if abs(angle_to_turn_to) > rotate_margin:

            # [ACTIVE] IF NOT ALREADY TURNING
            if self.action != "turn-right" and self.action != "turn-left":
                self.bot_rotate_to_direction(dir_to_turn)
                self.action = dir_to_turn

                if dir_to_turn == "turn-left":
                    print "ROTATE: <<<"
                elif dir_to_turn == "turn-right":
                    print "ROTATE: >>>"
                else:
                    print "Facing attacker - attacker slightly on : "+dir_to_turn+" side"

            # [PASSIVE] IF ALREADY TURNING
            else:
                pass
                #print self.action+" is still executing, angle to ball: "+str(angle_to_turn_to)

        # IF FACING OUR ATTACKER
        else:

            # [ACTIVE] IF STILL TURNING
            if self.action == "turn-right" or self.action == "turn-left":
                self.action = "idle"
                self.robotController.command(STOP_DRIVE_MOTORS)

                print "ROTATE: _ _ _"

            # [ACTIVE] IF FACING OUR ATTACKER && HAVE THE BALL
            if self.action == "idle" and self.state == "hasBall":
                self.action = "pass"
                self.robotController.command(GRABBER_OPEN)
                self.bot.catcher = "open"
                print "GRABBER: OPEN"
                # need to add a delay here?
                # possible alternatives
                sleep(0.5)
                self.robotController.command(PASS)
                print "PASS"

            # [PASSIVE] IF PASSING THE BALL && STILL HAS THE BALL
            elif self.action == "pass" and self.state == "hasBall":
                pass

            # [ACTIVE] IF PASSING THE BALL && NO LONGER HAS THE BALL
            elif self.action == "pass" and self.state != "hasBall":
                self.action = "idle"

    def fetch_ball(self):
        """
        (-dog mode)
        -open grabber when ball is in our zone and we're facing it
        -close grabber when in grabber area
        """
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
                    # [ACTIVE] IF TURNING BUT BALL CHANGED DIRECTION
                    pass

            # IF FACING BALL
            else:

                # [ACTIVE] IF STILL TURNING
                if (self.action == "turn-right" or self.action == "turn-left"):
                    self.bot_stop()

                # [ACTIVE] IF IDLE && OUTSIDE OF GRAB-RANGE && BALL INSIDE ZONE
                elif (self.action == "idle" and not inside_grabber and self.ball_inside_zone()):
                    self.action = "move-forward"
                    self.robotController.command(GRABBER_OPEN)
                    self.bot.catcher = "open"
                    self.robotController.command(MOVE_FORWARD)

                    print "MOVE: ^^^  &&  GRABBER: OPEN"

                # IF ALREADY MOVING FORWARD && OUTSIDE OF GRAB-RANGE
                elif (self.action == "move-forward" and not inside_grabber):

                    # [ACTIVE] IF BALL ROLLS OUT OF ZONE WHILE CHASING
                    if (not self.ball_inside_zone()):
                        self.bot_stop()

                    # [PASSIVE] BALL IN ZONE
                    else:
                        pass

                # [ACTIVE] IF MOVING FORWARD BUT INSIDE GRAB RANGE
                elif (self.action == "move-forward" and inside_grabber):
                    self.bot_stop()
                    self.bot_close_grabber()

                # [PASSIVE] IF IDLE && INSIDE GRAB-RANGE
                elif (self.action == "idle" and inside_grabber):
                    pass

            # [PASSIVE] IF BALL OUTSIDE ZONE
            if (not self.ball_inside_zone()):
                #print "Ball out of reach T.T "
                pass

    def defender_idle(self):
        """
        -create co-ord object in the middle of our defender zone
        -move to it
        -face towards their goal
        """
        our_zone = self.world.our_defender.zone

        # want to move to the middle of this zone
        x, y = our_zone.center()
        # deal with floats..
        idle_x = int(x)
        idle_y = int(y)

        idle_point = Coordinate(idle_x, idle_y)

        # TODO: code stolen from above - re-steal when updated work is committed

        rotate_margin = 0.75
        angle_to_turn_to = self.bot.get_rotation_to_point(idle_x, idle_y)
        dir_to_turn = self.get_direction_to_rotate(idle_point)

        if abs(angle_to_turn_to) > rotate_margin:

            # [ACTIVE] IF NOT ALREADY TURNING
            if self.action != "turn-right" and self.action != "turn-left":
                self.bot_rotate_to_direction(dir_to_turn)
                self.action = dir_to_turn

                if dir_to_turn == "turn-left":
                    print "ROTATE: <<<"
                elif dir_to_turn == "turn-right":
                    print "ROTATE: >>>"
                else:
                    print "Facing idle point - point slightly on : "+dir_to_turn+" side"

            # [PASSIVE] IF ALREADY TURNING
            else:
                pass
                #print self.action+" is still executing, angle to ball: "+str(angle_to_turn_to)

        # IF FACING OUR POINT
        else:

            # [ACTIVE] IF STILL TURNING
            if self.action == "turn-right" or self.action == "turn-left":
                self.action = "idle"
                self.robotController.command(STOP_DRIVE_MOTORS)

                print "ROTATE: _ _ _"

            # [ACTIVE] IF IDLE && NOT CLOSE TO POINT
            if self.action == "idle":
                self.action = "move-forward"
                self.robotController.command(MOVE_FORWARD)

                print "MOVE: ^^^"

            # [PASSIVE] IF ALREADY MOVING FORWARD && FAR FROM POINT POINT
            elif self.action == "move-forward" and self.bot_at_point(idle_point) == "far":
                pass

            # [ACTIVE] IF MOVING FORWARD && CLOSE TO POINT
            elif self.action == "move-forward" and self.bot_at_point(idle_point) == "close":
                self.action = "idle"
                self.robotController.command(STOP_DRIVE_MOTORS)

                print "MOVE: _ _ _"

            # [ACTIVE] IF IDLE && CLOSE TO POINT
            elif self.action == "idle" and self.bot_at_point(idle_point) == "close":
                rotate_margin = 0.75
                target = self.world.their_goal
                angle_to_turn_to = self.bot.get_rotation_to_point(target.x, target.y)
                dir_to_turn = self.get_direction_to_rotate(target)

                if abs(angle_to_turn_to) > rotate_margin:

                    # [ACTIVE] IF NOT ALREADY TURNING
                    if self.action != "turn-right" and self.action != "turn-left":
                        self.bot_rotate_to_direction(dir_to_turn)
                        self.action = dir_to_turn

                        if dir_to_turn == "turn-left":
                            print "ROTATE: <<<"
                        elif dir_to_turn == "turn-right":
                            print "ROTATE: >>>"
                        else:
                            print "Facing their goal - goal slightly on : "+dir_to_turn+" side"

                    # [PASSIVE] IF ALREADY TURNING
                    else:
                        pass

                # IF FACING THEIR GOAL
                else:

                    # [ACTIVE] IF STILL TURNING
                    if self.action == "turn-right" or self.action == "turn-left":
                        self.action = "idle"
                        self.robotController.command(STOP_DRIVE_MOTORS)

                        print "ROTATE: _ _ _"


    def bot_at_point(self, pitch_object):
        """
        Check if the bot is close to a given object
        Can expand for extra granularity (danger zone notion?)
        """
        movement_margin = 40

        if (abs(self.bot.x - pitch_object.x) > movement_margin) or (abs(self.bot.y - pitch_object.y) > movement_margin):
            return "far"
        else:
            return "close"

    def defender_mark_attacker(self):
        """
        -face towards their goal
        -move to the middle of our zone, x-axis-wise
        -strafe left/right depending on their attacker's position
        """
        self.bot_lock_y()

        bot = self.bot
        threat = self.world.their_attacker

        if threat.y > bot.y + 25:
            pass
        elif threat.y < bot.y - 25:
            pass

    def bot_lock_y(self):
        """
        Has the bot face their goal, and then stay locked to moving only on the Y-axis
        """
        self.bot_look_at(self.world.their_goal, 0.75)

        target_x, y = self.bot.zone.center
        bot_x = self.bot.x
        if bot_x > target_x + 25:
            self.bot.command(MOVE_FORWARD)
        elif bot_x < target_x + -25:
            self.bot.command(MOVE_BACK)

    def defender_block(self):
        """
        -face towards their goal
        -move to the middle of our zone, x-axis-wise
        -create a line from the angle of their robot to the middle of our defending zone
        -strafe left/right to get to the point where the line intersects our the vertical center of our zone
        """
        self.bot_lock_y()