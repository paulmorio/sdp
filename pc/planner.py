from math import pi, sqrt
from worldmodel import *

# Methods that 

class Planner():

    # MILESTONE
    def __init__(self, world, robotController, mode):
        self.world = world
        self.mode = mode
        self.state = None  # refactor planner into strategies at some point - not important for this milestone

        # Our controllable robot (ie. NOT OBSERVED, but ACTUAL arduino one)
        self.robotController = robotController

        # bot we are making plans for, OBSERVED robot via the vision.
        if (self.mode == 'attacker'):
            self.bot = self.world.our_attacker()
        elif(self.mode == 'defender'):
            self.bot = self.world.our_defender()
        elif(self.mode == 'dog'):
            self.bot = self.world.our_attacker()
        else:
            print "Not recognized mode!"

    def get_direction_to_rotate(self, pitch_object):
        """
        Returns a string indicating which direction to turn clockwise/a-clockwise depending on angle
        """
        angle = self.bot.get_rotation_to_point(pitch_object.x, pitch_object.y)

        if angle > 0.1:  # If the angle is greater than bearing + ~6 degrees, rotate CLKW (towards origin)
            return 'right'
        elif angle < -0.1:  # If the angle is less than bearing - ~6 degrees, rotate ACLKW (away from origin)
            return 'left'
        else:
            return 'none'

    # This method is likely unnecessary but kept because it is used in teuns dog implementation.
    def bot_rotate_to_direction(self, direction):
        """
        Rotates bot towards given direction

        needs more clarification on how much to turn etc based on refresh of world
        or on some time factor, or some amount to turn.
        """
        if direction == 'right':
            self.robotController.command(Robot.ROTATE_RIGHT)
        elif direction == 'left':
            self.robotController.command(Robot.ROTATE_LEFT)
        elif direction == 'none':
            self.robotController.command(Robot.STOP)
        else:
            print "ERROR in get_direction_to_rotate"

    # Issue11
    def bot_rotate_or_move(self, direction):
        """
        Rotates bot towards given direction, or moves forward if the direction is none
        """
        if direction == 'right':
            self.robotController.command(Robot.ROTATE_RIGHT)
        elif direction == 'left':
            self.robotController.command(Robot.ROTATE_LEFT)
        elif direction == 'none':
            self.robotController.command(Robot.MOVE_FORWARD)
        else:
            print "ERROR in get_direction_to_rotate"

    # Issue11
    def bot_get_ball(self):
        """
        Has the bot move to the ball, and grab it
        """
        ball = self.world._ball

        # We have to make sure we dont have the ball already
        if not self.bot.has_ball:
                    # If the robot cannot catch the ball yet
            if not self.bot.can_catch_ball(ball):
                dir_to_rotate = self.get_direction_to_rotate(ball)
                self.bot_rotate_and_go(dir_to_rotate)

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
            self.bot_rotate(dir_to_rotate)
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
            self.bot_rotate(dir_to_rotate)
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
                self.robotController.command(Robot.ROTATE_LEFT)
            elif angle > desired + 0.1:
                self.robotController.command(Robot.ROTATE_RIGHT)

            # if the balls ~y co-ord is bigger than ours, move forwards to intercept
            # if the balls ~y co-rds is less than ours, move backwards to intercept
            if ball.y > self.bot.y + 5:
                self.robotController.command(Robot.MOVE_FORWARD)
            elif ball.y < self.bot.y - 5:
                self.robotController.command(Robot.MOVE_BACK)

    # DEPRECATED?
    def attacker(self):
        """
        Have the robot move to and grab a stationary ball, then rotate to face a goal and kick it

        First step similar to "Dog" idea - robot turns to face ball, moves close to it
        Robot then grabs the ball, rotates towards the leftmost goal, and shoots
        """
        ball = self.world.ball

        if not self.bot.has_ball(ball):
            self.bot_get_ball()
        else:
            self.bot.own_goal()

    # DEPRECATED?
    def defender(self):
        """
        Have the robot stay on one axis until the ball is in its zone
        Once the ball is within our zone, move to it, grab it, and pass
        """
        ball = self.world.ball

        # If the ball is not in our zone, stay mobile
        if not self.world.pitch.zones[self.world.our_defender.zone].isInside(ball.x, ball.y):
            self.bot_intercept_shot()
        # Otherwise, if the ball is in our zone, move to it, grab it, and pass
        else:
            self.bot_get_ball()
            self.bot_pass_forward()


    # DEPRECATED?
    def chase(self):
        """
        Simple function to have robot go to ball (regardless of competition constraints)

        Basic "Dog" planning:
        Get co-ordinates of ball
        Get co-ordinates of robot
        Rotate-first method:
            1. Get angle between [ball.x, ball.y] and [robot.x, robot.y] as a bearing, using (robot.x, robot.y) as relative origin, x-axis(+) being 0 rad
            2. Rotate robot clockwise/anticlockwise (clockwise if robot angle > bearing, a-clockwise otherwise) until robot angle ~= bearing
            3. Move forwards until robot co-ords ~= ball co-ords, or angle changes
            4. If angle changes, go back to 1

        Holonomic method:
            1. Get angle between [ball.x, ball.y] and [robot.x, robot.y] as a bearing, using (robot.x, robot.y) as origin, x-axis(+) being 0 rad
            2. Move at that angle until robot co-ords ~= ball co-ords, or angle changes
            3. If angle changes, go back to 1
        """


    #     # Get displacement, and the ball
    #     ball = self.world.ball
    #     displacement = self.bot.get_displacement_to_point(self.world.ball.x, self.world.ball.y)

    #     if displacement > 20:  # 20 here is completely arbitrary, it should be a "safe" distance at which the robot can stop in front of the ball
    #         # Rotate-first
    #         dir_to_rotate = self.get_direction_to_rotate(ball)
    #         self.bot_rotate_and_go(dir_to_rotate)

    #         """
    #          # Holonomic TODO
    #          self.bot.commad(self.bot.MOVE_ANGLE + ()) etc..
    #         """
    #     else:
    #         self.bot.command(self.bot.STOP)

    # def aiming_towards_object(self, instance):
    #     # returns true if bot direction is towards instance
    #     return (instance)

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

        #TODO FOR WHOEVER DOES DEFENDER
        if self.mode == 'defender':

            ball_x = self.world._ball.x()
            ball_y = self.world._ball.y()
            pass



    # UPDATED "TICK" function 
    def updatePlan(self):
        """
        Makes plans based on the mode of the planner, and the state determined
        by the current situation (which can be found through determine_state)
        """

        # find out situation of robot (mode)
        self.state = determine_state(self.mode)

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
            if (self.state == 'hasBall'):
                rotate_towards_goal_and_shoot()

            # State when the ball is in possession of the opponents defender
            # Time to shadow the opponent defender.
            if (self.state == 'opponentDefenderHasBall'):
                defen_x = self.world.their_defender()._x
                defen_y = self.world.their_defender()._y

                #idea is to keep aligned with them along one axis and shadow movement
                bot_shadow_target()

            # State where the ball in possession of our defender
            # Time to shadow our defender so that ball comes to our possession.
            if (self.state == 'ourDefenderHasBall'):
                defen_x = self.world.our_defender()._x
                defen_y = self.world.our_defender()._y

                #idea is to keep aligned with them along one axis and shadow movement
                bot_shadow_target()

        # Find the different situations (states) the defender can be in
        elif self.mode == 'defender':

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
                        self.mode = 'Dog' # FETCH!! (WARNING: doggie style does not care about our field in the pitch)

        # # Dog mode
        # elif self.mode == 'Dog':
        #     if (self.state == 'noBall'):
        #         # implement chase
        #         if (not aiming_towards_object(ball)):
        #             self.robotController.rotate_towards_point(ball._x,ball._y)
        #         else: # Our robot is aiming towards the ball
        #             if (not robot_in_danger_zone()):
        #                 distance_to_ball = self.bot.get_displacement_to_point(ball._x,ball._y)
        #                 danger_zone_radius = 0 # personal space of ball (ie. radius around ball)
        #                 self.robotController.move_foward(distance_to_ball - danger_zone_radius,100) #100 = engine percentage: full throttle
        #             else: # Our robot is inside dangerzone of the ball, careful now, engines on low and approach with caution
        #                 if (not is_grabber_opened):
        #                     self.robotController.open_grabbers()
        #                 distance_to_ball = distance_to_ball = self.bot.get_displacement_to_point(ball._x,ball._y)
        #                 if (not distance_to_ball == 0):
        #                     self.robotController.move_foward(distance_to_ball - danger_zone_radius, 25)
        #                 else:
        #                     if (is_grabber_opened()):
        #                         self.robotController.close_grabbers()
        #                     self.state = 'hasBall'

        # ### FUNCTIONS TO DEFINE ###
        # #TESTING FUNTIONS
        # # aiming_towards_object(object) = TRUE if robot aims towards specified object (ie direction towards that point..)
        # # robot_in_danger_zone() = TRUE if robot is inside ball's personal space
        # # is_grabber_opened() = TRUE if grabbers are open
        # # ball_is_owned() = TRUE if ANY robot (THAT IS NOT OURS) on the field has the ball in posession (grabbed)
        # # ball_is_idle() = TRUE if ball is 'idle': ball is just lying around passively with specific negligable speed (thus not threatening to reach our goal)
        # #########
        # #ACTION FUNCTIONS
        # # rotate_towards_point(ball._x,ball.face_y) #rotates to aim towards given x,y coordinate.
        # # move_foward(distance, speed) #move robot forward for given distance, at a given speed
        # # move_vertical(y) = moves robot to given y-coordinate. (y = pixel coordinate)
        # # open_grabbers() #duhh..
        # # close_grabbers() #another duhh
        # #MISC FUNCTION
        # # pitch_get_height() = returns height of pitch (in pixels)

        # No Danger Zone here.
        # Dog Mode for robot. NB: This is hacked together it would be better to move this into seperate functions
        elif (self.mode == 'dog'):

            # If the robot does not have the ball, it should go to the ball.
            if (self.state == 'noBall'):
                # Get the ball position so that we may find the angle to align with it, as well as the displacement
                ball_x = self.world._ball.x()
                ball_y = self.world._ball.y()

                angle_to_turn_to = self.bot.get_rotation_to_point(ball_x,ball_y)
                distance_to_move = self.bot.get_displacement_to_point(ball_x, ball_y)

                dir_to_turn = get_direction_to_rotate(self.world._ball)

                # We command the robot turn to the ball, and move forward if it is facing it.
                # This is implementation is deeply simplified (but works)
                bot_rotate_or_move(dir_to_turn)

                # Better would be being able to turn or move forward using information gained in the frame
                # bot_rotate_or_move(dir_to_turn, angle_to_turn_to, distance_to_move)

            else;
                print "Error, cannot find mode"
            
