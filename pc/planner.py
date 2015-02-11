from models.worldmodel import *
from robot import *
from time import sleep


class Planner():

    # MILESTONE
    def __init__(self, world, robot_controller, mode):
        self.world = world
        self.mode = mode
        self.state = None

        self.antiflood_limit = 5
        self.antiflood_counter = self.antiflood_limit

        #PENALTY CASE FOR MILESTONE
        if self.mode == "defender":
            self.ball_mode = "stopped"

        # for our dear toy example, he never has the ball
        if self.mode == 'dog':
            self.shoot_target = "goal"
            self.init_dog()
        elif self.mode == "attacker":
            self.shoot_target = "goal"
        elif self.mode == "defender":
            self.shoot_target = "attackerzone"


        # action the robot is currently executing:
        self.action = "idle"
        # none
        # turn-left
        # turn-right
        # move-forward
        # crawl-forward
        # move-back
        # strafe-left
        # strafe-right
        ## grabbing # essentially replaced by
        ## releasing
        # shooting
        # passing

        self.final_countdown = -1

        # Our controllable robot (ie. NOT OBSERVED, but ACTUAL arduino one)
        self.robot_controller = robot_controller
        self.robotStarted = 60  # init robot actions

        # bot we are making plans for, OBSERVED robot via the vision.
        if self.mode == 'attacker':
            self.bot = self.world.our_attacker
        elif self.mode == 'defender':
            self.bot = self.world.our_defender
        elif self.mode == 'dog':
            self.bot = self.world.our_attacker
        else:
            print "Not recognized mode!"

        self.bot.catcher = "closed"

    def init_dog(self):
        self.state = 'noBall'
        self.final_countdown = -1
    ################################
    ########## SUBPLANS ############
    ################################

    def inside_grabber(self):
        ball = self.world.ball
        return self.bot.can_catch_ball(ball)

    def inside_friendly_space(self, distance):
        ball = self.world.ball
        return abs(ball.get_displacement_to_point(self.bot.x, self.bot.y)) \
            < distance

    def ball_inside_zone(self):
        ball = self.world.ball
        return self.world.pitch.is_within_bounds(self.bot, ball.x, ball.y)

    def robot_inside_zone(self):
        print "("+str(self.bot.x)+","+str(self.bot.y)+")"
        print str(self.world.pitch.zones[self.bot.zone].isInside(self.bot.x, self.bot.y))
        return True

    def get_direction_to_rotate(self, pitch_object):
        """
        Returns a string indicating which direction to turn
        clockwise/a-clockwise (right/left) depending on angle
        """
        angle = self.bot.get_rotation_to_point(pitch_object.x, pitch_object.y)

        if angle <= 0:
            return 'turn-right'
        elif angle > 0:
            return 'turn-left'
        else:
            return 'none'

    def bot_rotate_to_direction(self, direction):
        """
        Rotates bot towards given direction

        needs more clarification on how much to
        turn etc based on refresh of world
        or on some time factor, or some amount to turn.
        """
        if direction == 'turn-right':
            self.robot_controller.command(TURN_RIGHT)
            self.bot.action = 'turn-right'
            print "ROTATE: >>>"
        elif direction == 'turn-left':
            self.robot_controller.command(TURN_LEFT)
            self.bot.action = 'turn-left'
            print "ROTATE: <<<"
        elif direction == 'none':  # This code should never execute
            self.robot_controller.command(STOP_DRIVE_MOTORS)
            self.bot.action = 'idle'
        else:
            print "ERROR in get_direction_to_rotate"

    def bot_look_at(self, pitch_object, rotate_margin):
        """
        Has the ball turn and face an object, returning True when facing,
        False otherwise

        :param pitch_object: the object to face
        :type pitch_object: anything with .x, .y properties
        :param rotate_margin: (radians) the cone in which the robot is
            considered to be facing the object
        :type rotate_margin: float
        :return: boolean
        """

        angle_to_turn_to = \
            self.bot.get_rotation_to_point(pitch_object.x, pitch_object.y)

        dir_to_turn = self.get_direction_to_rotate(pitch_object)

        # IF NOT FACING OBJECT
        if abs(angle_to_turn_to) > rotate_margin:

            # [ACTIVE] IF NOT ALREADY TURNING
            if self.action != "turn-right" and self.action != "turn-left":
                self.bot_rotate_to_direction(dir_to_turn)

                if dir_to_turn == "turn-left":
                    print "ROTATE: <<<"
                elif dir_to_turn == "turn-right":
                    print "ROTATE: >>>"
                else:
                    print "Facing object - object slightly on : " \
                          + dir_to_turn+" side"

            # [PASSIVE] IF ALREADY TURNING
            else:
                pass

            return False

        # IF FACING OBJECT
        else:

            # [ACTIVE] IF STILL TURNING
            if self.action == "turn-right" or self.action == "turn-left":
                self.bot_stop()
            return True

    def aiming_towards_object(self, instance):
        # returns true if bot direction is towards instance
        if abs(self.bot.get_rotation_to_point(instance.x, instance.y)) > 0.1:
            return False
        else:
            return True

    #################################
    ########## AGGREGATORS ##########
    #################################

    def determine_state(self):
        """
        This method determines the state of the robot given the robots mode, 
        and the situation on the pitch
        """

        if self.mode == 'attacker':

            ball_x = self.world.ball.x
            ball_y = self.world.ball.y

            if self.world.pitch.is_within_bounds(self.bot, ball_x, ball_y):
                return 'inZone'

            elif self.bot.has_ball(self.world.ball):
                return 'hasBall'

            else:
                return 'other'

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

            if self.world.pitch.is_within_bounds(self.world.their_attacker, ball_x, ball_y):
                return 'inTheirAttackerZone'

            # Our defender has possession
            if self.bot.has_ball(self.world.ball):
                return 'hasBall'

            # Our attacker has the ball
            if self.world.our_attacker.has_ball(self.world.ball):
                return 'ourAttackerHasBall'

            # etc..
            if self.world.their_defender.has_ball(self.world.ball):
                return 'opponentDefenderHasBall'

            if self.world.their_attacker.has_ball(self.world.ball):
                return 'opponentAttackerHasBall'

    def bot_stop(self):
        self.robot_controller.command(STOP_DRIVE_MOTORS)
        self.action = "idle"
        print "MOVE: STOPPED!"

    def bot_open_grabber(self):
        if not self.bot.catcher == "open":
            self.robot_controller.command(GRABBER_OPEN)
            self.bot.catcher = "open"
            print "GRABBER: OPEN"

    def bot_close_grabber(self):
        if not self.bot.catcher == "closed":
            self.state = 'hasBall'
            self.robot_controller.command(GRABBER_CLOSE)
            self.bot.catcher = "closed"
            print "GRABBER: CLOSE"

    # UPDATED "TICK" function 
    def update_plan(self):
        """
        Makes plans based on the mode of the planner, and the state determined
        by the current situation (which can be found through determine_state)
        """
        # CHECK IF ROBOT IS READY

        if self.robotStarted > 0:
            self.robotStarted -= 1
            print "NUKE IN .."+str(self.robotStarted)

            if not self.mode == "defender":
                if self.robotStarted == 10:
                    self.bot_open_grabber()

                if self.robotStarted == 5:
                    self.bot_open_grabber()
        else:



            if self.antiflood_counter > 0:
                self.antiflood_counter -= 1
            else:
                #print "TICK!"
                self.antiflood_counter = self.antiflood_limit

                # find out situation of robot (mode)
                if self.mode != "dog":
                    self.state = self.determine_state()

                # Attacker mode
                if self.mode == "attacker":

                    # IF BALL IN ZONE
                    if self.state == 'inZone':
                        self.fetch_ball()
                    elif self.state == 'hasBall':
                        self.basic_shoot()
                    elif self.state == 'other':
                        self.bot_stop()

                # Defender mode
                elif self.mode == "defender":

                    # DEFINE BALL STATES (in penalty case)
                    if self.ball_mode == "stopped":
                        if self.ball_moving() and not self.state == "inZone":
                            self.ball_mode = "incoming"

                    elif self.ball_mode == "incoming" and not self.ball_moving() and not self.state=="inZone":
                        self.ball_mode = "stopped"

                    elif self.ball_mode == "incoming" and not self.ball_moving() and self.state=="inZone":
                        self.ball_mode = "caught"

                    # IF BALL IS INCOMING
                    if self.ball_mode == "incoming":

                        self.bot_open_grabber()
                        # AIM ROBOT TOWARDS ENEMY GOAL
                        # create fake pitch object with bot x, large y-co-ord

                        target_x = self.bot.x
                        target_y = 1000  # arbitrarily large

                        ##edit
                        angle_to_turn_to = self.bot.get_rotation_to_point(self.bot.x, self.world.our_goal.y)
                        dir_to_turn = self.get_direction_to_rotate(self.world.our_goal)
                        ##edit

                        target_point = Coordinate(target_x, target_y)

                        # IF NOT FACING BALL
                        if (abs(angle_to_turn_to) > 0.50):

                        # # IF WE ARE FACING THE POINT
                        # if self.bot_look_at(target_point, 0.50):

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

                        # IF FACING GOAL
                        else:
                            # [ACTIVE] IF STILL TURNING
                            if (self.action == "turn-right" or self.action == "turn-left"):
                                self.bot_stop()

                            elif self.action != "move-forward":

                                if abs(self.bot.y - self.world.our_goal.y) > 30:
                                    self.action = "move-forward"
                                    self.robot_controller.command(MOVE_FORWARD)

                                else:
                                    self.bot_stop()






                            # # IF ROBOT TOO FAR FROM PREDICTED BALL-Y-COORDINATE
                            # if abs(self.bot.y - self.ball_predict_y()) > 15:
                            #
                            #     # IF BALL-PREDICTED-Y ABOVE ROBOT
                            #     if self.ball_predict_y() > self.bot.y:
                            #
                            #         # [ACTIVE] MOVE FORWARD (UP)
                            #         if self.action != "move-forward":
                            #             self.action = "move-forward"
                            #             self.robot_controller.command(MOVE_FORWARD)
                            #
                            #         # [PASSIVE] IF MOVING FORWARD
                            #         elif self.action == "move-forward":
                            #             pass

                                    # STRAFE CODE
                                    # # IF BALL LEFT OF ROBOT
                                    # if self.world.ball.x < self.bot.x:
                                    #
                                    #     # [ACTIVE] STRAFE RIGHT (robot moves up)
                                    #     if self.action != "strafe-right":
                                    #         self.action = "strafe-right"
                                    #         self.robot_controller.command(STRAFE_RIGHT)
                                    #
                                    #         print "----"
                                    #         print "BOT: ("+str(self.bot.x)+","+str(self.bot.y)+")"
                                    #         print "BALL: ("+str(self.world.ball.x)+","+str(self.world.ball.y)+")"
                                    #         print "FUTURE_BALL: ("+str(self.bot.x)+","+str(self.ball_predict_y())+")"
                                    #         print "BALL_ANGLE: "+str(self.world.ball.angle)
                                    #         print "trying to catch ball on its right"
                                    #     # [PASSIVE]
                                    #     else:
                                    #         pass
                                    #
                                    # # IF BALL RIGHT OF ROBOT
                                    # else:
                                    #     # [ACTIVE] STRAFE LEFT (robot moves up)
                                    #     if (self.action != "strafe-left"):
                                    #         self.action = "strafe-left"
                                    #         self.robot_controller.command(STRAFE_LEFT)
                                    #
                                    #         print "----"
                                    #         print "BOT: ("+str(self.bot.x)+","+str(self.bot.y)+")"
                                    #         print "BALL: ("+str(self.world.ball.x)+","+str(self.world.ball.y)+")"
                                    #         print "FUTURE_BALL: ("+str(self.bot.x)+","+str(self.ball_predict_y())+")"
                                    #         print "BALL_ANGLE: "+str(self.world.ball.angle)
                                    #         print "trying to catch the ball on its left"
                                    #     # [PASSIVE]
                                    #     else:
                                    #         pass

                                # IF BALL-PREDICTED-Y BELOW ROBOT
                                # else:
                                #
                                #     # [ACTIVE] MOVE BACK (DOWN)
                                #     if self.action != "move-back":
                                #         self.action = "move-back"
                                #         self.robot_controller.command(MOVE_BACK)
                                #
                                #     # [PASSIVE] IF MOVING BACK
                                #     elif self.action == "move-back":
                                #         pass

                                    # STRAFE CODE
                                    # # IF BALL LEFT OF ROBOT
                                    # if self.world.ball.x < self.bot.x:
                                    #
                                    #     # [ACTIVE] STRAFE LEFT (robot moves down)
                                    #     if (self.action != "strafe-left"):
                                    #         self.action = "strafe-left"
                                    #         self.robot_controller.command(STRAFE_LEFT)
                                    #
                                    #         print "----"
                                    #         print "BOT: ("+str(self.bot.x)+","+str(self.bot.y)+")"
                                    #         print "BALL: ("+str(self.world.ball.x)+","+str(self.world.ball.y)+")"
                                    #         print "FUTURE_BALL: ("+str(self.bot.x)+","+str(self.ball_predict_y())+")"
                                    #         print "BALL_ANGLE: "+str(self.world.ball.angle)
                                    #         print "trying to catch ball on its left"
                                    #     # [PASSIVE]
                                    #     else:
                                    #         pass
                                    #
                                    # # IF BALL RIGHT OF ROBOT
                                    # else:
                                    #
                                    #     # [ACTIVE] STRAFE RIGHT (robot moves down)
                                    #     if (self.action != "strafe-right"):
                                    #         self.action = "strafe-right"
                                    #         self.robot_controller.command(STRAFE_RIGHT)
                                    #
                                    #         print "----"
                                    #         print "BOT: ("+str(self.bot.x)+","+str(self.bot.y)+")"
                                    #         print "BALL: ("+str(self.world.ball.x)+","+str(self.world.ball.y)+")"
                                    #         print "FUTURE_BALL: ("+str(self.bot.x)+","+str(self.ball_predict_y())+")"
                                    #         print "BALL_ANGLE: "+str(self.world.ball.angle)
                                    #         print "trying to catch ball on its right"
                                    #     # [PASSIVE]
                                    #     else:
                                    #         pass

                            # # ROBOT IS IN THE RIGHT POSITION TO CATCH BALL
                            # elif not self.action == "idle":
                            #     print "ROBOT IN RIGHT POSITION. WAITING FOR ARRIVAL"
                            #     self.bot_stop()

                    elif self.ball_mode == "stopped" and not self.action == "idle":
                        self.bot_stop()

                    # IF BALL WAS CAUGHT BY ROBOT
                    elif self.ball_mode == 'caught':
                        self.mode = "dog"
                        self.init_dog()


                    # DEFENDER CODE, NOT IN USE FOR MILESTONE 2! BUT KEEP HERE
                    # # TODO:
                    # # Awaiting future refactorings
                    # if self.state == 'inZone':
                    #     if self.state == 'hasBall':
                    #         self.pass_forward()
                    #     else:
                    #         self.fetch_ball()
                    # elif self.state == 'inOurAttackerZone':
                    #     self.defender_idle()
                    # elif self.state == 'inTheirDefenderZone':
                    #     self.defender_idle()
                    # elif self.state == 'inTheirAttackerZone':
                    #     self.defender_mark_attacker()
                    #
                    # elif self.state == 'ourAttackerHasBall':
                    #     self.defender_idle()
                    # elif self.state == 'opponentDefenderHasBall':
                    #     self.defender_idle()
                    # elif self.state == 'opponentAttackerHasBall':
                    #     self.defender_block()

                # Dog Mode for robot. NB: This is hacked together it would be better to move this into seperate functions
                if (self.mode == 'dog'):

                    # Get the ball position so that we may find the angle to align with it, as well as the displacement
                    ball_x = self.world._ball.x
                    ball_y = self.world._ball.y
                    friendly_space = 70
                    rotate_margin = 0.50
                    inside_grabber = self.inside_grabber()

                    # If the robot does not have the ball, it should go to the ball.
                    if (self.state == 'noBall'):

                        angle_to_turn_to = self.bot.get_rotation_to_point(ball_x,ball_y)
                        dir_to_turn = self.get_direction_to_rotate(self.world._ball)

                        # IF NOT FACING BALL
                        if (abs(angle_to_turn_to) > rotate_margin):
                            #print "open at 3"
                            #self.bot_open_grabber()

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

                        # IF FACING BALL
                        else:

                            # [ACTIVE] IF STILL TURNING
                            if (self.action == "turn-right" or self.action == "turn-left"):
                                self.bot_stop()

                            # [ACTIVE] IF IDLE && OUTSIDE OF GRAB-RANGE && BALL INSIDE ZONE
                            elif (self.action == "idle" and not inside_grabber and self.ball_inside_zone()):
                                self.action = "crawl-forward"
                                self.robot_controller.command(CRAWL_FORWARD)

                                print "CRAWL: ^^^"

                                # [ACTIVE] IF BALL IS CLOSE CLOSE GRABBER
                                if (self.bot.get_displacement_to_point(self.world.ball.x, self.world.ball.y) < 60):
                                    print "PRE-CLOSING GRABBER ________"
                                    self.bot_close_grabber()
                                # [ACTIVE] (ELSE) IF BALL IS TOO FAR AWAY OPEN GRABBER
                                else:
                                    print "open at 1"
                                    self.bot_open_grabber()

                            # IF ALREADY MOVING FORWARD && OUTSIDE OF FRIENDLY-SPACE
                            elif (self.action == "crawl-forward" and not inside_grabber):

                                # [ACTIVE] IF BALL ROLLS OUT OF ZONE WHILE CHASING
                                if (not self.ball_inside_zone()):
                                    self.bot_stop()


                                # [PASSIVE] BALL IN ZONE
                                else:
                                    pass

                            # [ACTIVE] IF MOVING FORWARD BUT INSIDE GRAB RANGE
                            elif (self.action == "crawl-forward" and inside_grabber):
                                print "IN GRABBER RANGE"
                                self.action = "idle"
                                self.bot_stop()
                                self.bot_close_grabber()

                            # [ACTIVE] IF IDLE && INSIDE GRAB-RANGE
                            elif (self.action == "idle" and inside_grabber):
                                print "CAUGHT BALL"
                                self.state = 'hasBall'
                                self.bot_close_grabber()

                        # [PASSIVE] IF BALL OUTSIDE ZONE
                        if (not self.ball_inside_zone()):
                            #print "Ball out of reach T.T "
                            pass

                    # IF ROBOT HAS BALL
                    elif self.state == 'hasBall':

                        if not inside_grabber:
                            self.state = "noBall"

                        print "countdown: "+str(self.final_countdown)

                        # IF BALL IMPOSSIBLY FAR FROM ROBOT
                        if (abs(self.bot.get_displacement_to_point(self.world.ball.x, self.world.ball.y)) > 50):
                            print "LOSING THE BALL, OUT OF RANGE."
                            self.state = "noBall"

                        angle_to_turn_to = self.bot.get_rotation_to_point(self.world.their_goal.x, self.world.their_goal.y)
                        dir_to_turn = self.get_direction_to_rotate(self.world.their_goal)

                        # IF NOT LOOKING AT ENEMY GOAL
                        if abs(angle_to_turn_to) > 0.30:
                            self.bot_close_grabber()

                            # IF NOT ALREADY ROTATING
                            if self.action != "turn-right" and self.action != "turn-left":

                                # [ACTIVE] ROTATE TO ENEMY GOAL
                                self.bot_rotate_to_direction(dir_to_turn)
                                self.action = dir_to_turn

                                if dir_to_turn == "turn-left":
                                    print "ROTATE: <<<"
                                elif dir_to_turn == "turn-right":
                                    print "ROTATE: >>>"
                                else:
                                    print "Facing goal - object slightly on : "+dir_to_turn+" side"

                            # IF ROTATING TO ENEMY GOAL
                            else:
                                self.bot_rotate_to_direction(dir_to_turn)
                                self.action = dir_to_turn
                                # # [ACTIVE] IF BALL NO LONGER INSIDE GRABBER AREA
                                # if not self.inside_grabber():
                                #     print "LOST BALL"
                                #     self.state = "noBall"

                        # IF LOOKING AT ENEMY GOAL
                        else:
                            self.bot_stop()
                            # [CONSTANT] DECREMENT FINAL_COUNTDOWN IF APPLICABLE
                            if self.final_countdown > 0:
                                print "FINAL COUNTDOWN: "+str(self.final_countdown)
                                self.final_countdown -= 1

                            # [ACTIVE] IF GRABBER STILL CLOSED
                            if self.bot.catcher == "closed" and self.final_countdown < 0:
                                print "AIM AT GOAL, OPEN GRABBER, PREPARING SHOT!"
                                print "angle to goal: "+str(abs(angle_to_turn_to))+" > 0.30"

                                self.final_countdown = 10
                                self.bot_stop()


                            if self.final_countdown == 0:
                                self.bot_open_grabber()
                                if self.shoot_target=="attackerzone":
                                    self.robot_controller.command(PASS)
                                else:
                                    self.robot_controller.command(SHOOT)
                                self.final_countdown = -1

                                # IF DEFENDER AND TRYING TO SHOOT INTO ATTACKER ZONE:
                                if self.shoot_target=="attackerzone":
                                    self.robot_controller.command(PASS)
                                else:
                                    self.robot_controller.command(SHOOT)

                                self.state = "noBall"


                            # # IF BALL INSIDE GRABBER AREA
                            # if self.inside_grabber():
                            #
                            #     # [ACTIVE] IF GRABBER STILL CLOSED
                            #     if self.bot.catcher == "closed":
                            #         print "AIM AT GOAL, OPEN GRABBER, PREPARING SHOT!"
                            #         print "angle to goal: "+str(abs(angle_to_turn_to))+" > 0.50"
                            #
                            #         self.bot_open_grabber()
                            #
                            #     # [ACTIVE] IF GRABBER OPEN
                            #     else:
                            #         self.robot_controller.command(SHOOT)
                            #
                            # # [ACTIVE] IF BALL NOT IN GRABBER AREA
                            # else:
                            #     print "LOST BALL"
                            #     self.state = "noBall"

                    else:
                        print "Error, state unknown: "+str(self.state)

    def pass_forward(self):
        """
        -rotate to face our attacker
        -open grabber, pass ball
        # assumes there's no obstacles in the way, for the moment
        """

        # TODO: code stolen from above - re-steal when updated work is committed
        rotate_margin = 0.50
        our_attacker = self.world.our_attacker
        angle_to_turn_to = self.bot.get_rotation_to_point(our_attacker.x, our_attacker.y)
        dir_to_turn = self.get_direction_to_rotate(self.world.ball)

        if abs(angle_to_turn_to) > rotate_margin:

            # [ACTIVE] IF NOT ALREADY TURNING
            if self.action != "turn-right" and self.action != "turn-left":
                self.bot_rotate_to_direction(dir_to_turn)

                if dir_to_turn == "turn-left":
                    print "ROTATE: <<<"
                elif dir_to_turn == "turn-right":
                    print "ROTATE: >>>"
                else:
                    print "Facing attacker - attacker slightly on : " + dir_to_turn+" side"

            # [PASSIVE] IF ALREADY TURNING
            else:
                pass

        # IF FACING OUR ATTACKER
        else:

            # [ACTIVE] IF STILL TURNING
            if self.action == "turn-right" or self.action == "turn-left":
                self.action = "idle"
                self.robot_controller.command(STOP_DRIVE_MOTORS)

                print "ROTATE: _ _ _"

            # [ACTIVE] IF FACING OUR ATTACKER && HAVE THE BALL
            if self.action == "idle" and self.state == "hasBall":
                self.action = "passing"
                self.bot_open_grabber()
                # need to add a delay here?
                # possible alternatives
                sleep(0.5)
                self.robot_controller.command(PASS)
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
        rotate_margin = 0.50
        inside_grabber = self.inside_grabber()

        # IF FACING BALL
        if self.bot_look_at(self.world.ball, rotate_margin):
            # [ACTIVE] IF STILL TURNING
            if self.action == "turn-right" or self.action == "turn-left":
                self.bot_stop()

            # [ACTIVE] IF IDLE && OUTSIDE OF GRAB-RANGE && BALL INSIDE ZONE
            elif self.action == "idle" and not inside_grabber and self.ball_inside_zone():
                print "CRAWL: ^^^  &&  GRABBER: OPEN"
                self.action = "crawl-forward"
                self.bot_open_grabber()
                self.robot_controller.command(CRAWL_FORWARD)

            # IF ALREADY MOVING FORWARD && OUTSIDE OF GRAB-RANGE
            elif self.action == "crawl-forward" and not inside_grabber:

                # [ACTIVE] IF BALL ROLLS OUT OF ZONE WHILE CHASING
                if not self.ball_inside_zone():
                    self.bot_stop()

                # [PASSIVE] BALL IN ZONE
                else:
                    pass

            # [ACTIVE] IF MOVING FORWARD BUT INSIDE GRAB RANGE
            elif self.action == "crawl-forward" and inside_grabber:
                self.bot_stop()
                self.bot_close_grabber()

            # [PASSIVE] IF IDLE && INSIDE GRAB-RANGE
            elif self.action == "idle" and inside_grabber:
                pass

        # IF NOT FACING BALL
        else:
            pass

        # [PASSIVE] IF BALL OUTSIDE ZONE
        if not self.ball_inside_zone():
            #print "Ball out of reach T.T "
            pass

    def defender_idle(self):
        """
        -create co-ord object in the middle of our defender zone
        -move to it
        -face towards their goal
        """
        our_zone = self.world.pitch.zones[self.bot.zone]

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
                self.robot_controller.command(STOP_DRIVE_MOTORS)

                print "ROTATE: _ _ _"

            # [ACTIVE] IF IDLE && NOT CLOSE TO POINT
            if self.action == "idle":
                self.action = "move-forward"
                self.robot_controller.command(MOVE_FORWARD)

                print "MOVE: ^^^"

            # [PASSIVE] IF ALREADY MOVING FORWARD && FAR FROM POINT POINT
            elif self.action == "crawl-forward" and self.bot_at_point(idle_point) == "far":
                pass

            # [ACTIVE] IF MOVING FORWARD && CLOSE TO POINT
            elif self.action == "crawl-forward" and self.bot_at_point(idle_point) == "close":
                self.action = "idle"
                self.robot_controller.command(STOP_DRIVE_MOTORS)

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
                        self.robot_controller.command(STOP_DRIVE_MOTORS)

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

        my_zone = self.world.pitch.zones[self.bot.zone]
        target_x, y = my_zone.center()
        bot_x = self.bot.x
        if bot_x > target_x + 25:
            self.action = "crawl-forward"
            self.robot_controller.command(CRAWL_FORWARD)
        elif bot_x < target_x + -25:
            self.robot_controller.command(CRAWL_BACK)
            self.action = "crawl-back"

    def defender_block(self):
        """
        -face towards their goal
        -move to the middle of our zone, x-axis-wise
        -create a line from the angle of their robot to the middle of our defending zone
        -strafe left/right to get to the point where the line intersects our the vertical center of our zone
        """
        self.bot_lock_y()

        if self.ball_moving():
            pass

    def basic_shoot(self):
        """
        -face towards their goal
        -shoot!
        """
        # Face towards their goal (assumes no obstacles)
        # True = facing goal, false = still rotating
        if self.bot_look_at(self.world.their_goal, 0.35):
                self.action = "shooting"
                self.bot_open_grabber()
                # need to add a delay here?
                # possible alternatives
                sleep(0.5)
                self.robot_controller.command(SHOOT)
                print "SHOOT"

        else:
            # [PASSIVE] IF STILL TURNING
            pass

    def ball_moving(self):
        return abs(self.world.ball.velocity) > 2

    # Return expected y-coordinate when ball reaches robot's X-position
    def ball_predict_y(self):
        ball = self.world.ball
        bot = self.bot

        if ball.angle == pi/2:
            return ball.y
        else:
            angle = ball.angle

        dy = (abs(bot.x-ball.x)*sin(angle)) / sin(pi/2 - angle)

        angle = divmod(angle, 2*pi)

        if pi/2 < angle < 3*pi/2:
            future_y = ball.y - dy
        else:
            future_y = ball.y + dy

        return future_y