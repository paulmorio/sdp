from math import pi, sqrt
from worldmodel import *

class Planner():

    # MILESTONE
    def __init__(self, world, robotController, mode):
        self.world = world
        self.mode = mode
        self.state = None  # refactor planner into strategies at some point - not important for this milestone

        # Our controllable robot (ie. NOT OBSERVED, but ACTUAL arduino one)
        self.robotcontroller = robotController

        # bot we are making plans for, OBSERVED robot via the vision.
        if (self.mode == 'attacker'):
            self.bot = self.world.our_attacker()
        elif(self.mode == 'defender'):
            self.bot = self.world.our_defender()
        elif(self.mode == 'dog'):
            self.bot = self.world.our_attacker()
        else:
            print "Not recognized mode!"

        self.get_default_state()

    # MILESTONE
    def get_default_state(self):
        if self.mode == 'attacker':
            self.state = 'catch'
        elif self.mode == 'defender':
            self.state = 'intercept'

        # Toy Mode (experimental)
        elif self.mode == 'chase':
            self.state = 'chase'

    # MILESTONE
    def tick(self):
        """
        Depending on the mode we're in, act out a plan
        """
        if self.bot is not None:
            if self.mode == 'attacker':
                self.attacker()
            elif self.mode == 'defender':
                self.defender()
            elif self.mode == 'chase':
                self.chase()
            else:
                print "Error - unknown mode!"

    # MILESTONE
    def get_rotation_direction(self, pitch_object):
        """
        Quick 'n' dirty - tells us if the robot needs to rotate to face an object (within ~6degrees of accuracy)
        """
        angle = self.bot.get_rotation_to_point(pitch_object.x, pitch_object.y)

        if angle > 0.1:  # If the angle is greater than bearing + ~6 degrees, rotate CLKW (towards origin)
            return 'right'
        elif angle < -0.1:  # If the angle is less than bearing - ~6 degrees, rotate ACLKW (away from origin)
            return 'left'
        else:
            return 'none'

    # MILESTONE
    def bot_rotate(self, direction):
        """
        Quick 'n' dirty - rotates bot towards given direction
        """
        if direction == 'right':
            self.bot.command(self.bot.ROTATE_RIGHT)
        elif direction == 'left':
            self.bot.command(self.bot.ROTATE_LEFT)
        elif direction == 'none':
            self.bot.command(self.bot.STOP)
        else:
            print "ERROR in get_rotation_direction"

    # MILESTONE
    def bot_rotate_and_go(self, direction):
        """
        Quick 'n' dirty - rotates bot towards given direction, or moves forward if the direction is none
        """
        if direction == 'right':
            self.bot.command(self.bot.ROTATE_RIGHT)
        elif direction == 'left':
            self.bot.command(self.bot.ROTATE_LEFT)
        elif direction == 'none':
            self.bot.command(self.bot.MOVE_FORWARD)
        else:
            print "ERROR in get_rotation_direction"

    # MILESTONE
    def bot_get_ball(self):
        """
        Quick 'n' dirty - has the ball move to the ball, and grab it
        """
        ball = self.world.ball

        if not self.bot.can_catch_ball(ball):  # If the ball is not within catching range, move towards it
            # If we need to rotate to face the ball, do so, otherwise just move to it
            dir_to_rotate = self.get_rotation_direction(ball)
            self.bot_rotate_and_go(dir_to_rotate)

        else:  # Otherwise (if the ball is within catching range) "grab" until we have possession of the ball
            if not self.bot.has_ball(ball):
                self.bot.command(self.bot.GRAB)

    def bot_own_goal(self):
        """
        Quick 'n' dirty - when the bot has possession of the ball, will cause it to rotate towards own goal and shoot
        """
        # Now that we have the ball, rotate towards the own goal.
        dir_to_rotate = self.get_rotation_direction(self.world.our_goal)
        if dir_to_rotate != 'none':  # If we need to rotate, do so
            self.bot_rotate(dir_to_rotate)
        else:  # Finished rotating to face goal, can now kick
            self.bot.command(self.bot.KICK)
            #self.bot.command(PREMATURE_CELEBRATION)

    # MILESTONE
    def bot_pass_forward(self):
        """
        Quick 'n' dirty - when the bot has possession of the ball, will cause it to rotate towards their goal and pass
        """
        # Now that we have the ball, rotate towards the right attacking zone.  # IMPORTANT: 'side' has to be 'left'
        dir_to_rotate = self.get_rotation_direction(self.world.their_goal)
        if dir_to_rotate != 'none':  # If we need to rotate, do so
            self.bot_rotate(dir_to_rotate)
        else:  # Finished rotating to face goal, can now kick
            self.bot.command(self.bot.PASS)  # TODO: pass? Can just replace with a "KICK" depending.

    # MILESTONE
    def bot_intercept_shot(self):
        """
        Quick 'n' dirty - when the ball is not in our defending zone, rotate to move on the y-axis only, and attempt to block any shot
        """
        ball = self.world.ball

        # If the ball is not in our zone, stay mobile
        if not self.world.pitch.zones[self.world.our_defender.zone].isInside(ball.x, ball.y):
            # face ~3/2pi angle, ie towards the bottom of the pitch
            angle = self.bot.angle
            desired = (3.0 / 2.0) * pi

            if angle < desired - 0.1:
                self.bot.command(self.bot.ROTATE_LEFT)
            elif angle > desired + 0.1:
                self.bot.command(self.bot.ROTATE_RIGHT)

            # if the balls ~y co-ord is bigger than ours, move forwards to intercept
            # if the balls ~y co-rds is less than ours, move backwards to intercept
            if ball.y > self.bot.y + 5:
                self.bot.command(self.bot.MOVE_FORWARD)
            elif ball.y < self.bot.y - 5:
                self.bot.command(self.bot.MOVE_BACK)

    # MILESTONE
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

    # MILESTONE
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


    # MILESTONE
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


        # Get displacement, and the ball
        ball = self.world.ball
        displacement = self.bot.get_displacement_to_point(self.world.ball.x, self.world.ball.y)

        if displacement > 20:  # 20 here is completely arbitrary, it should be a "safe" distance at which the robot can stop in front of the ball
            # Rotate-first
            dir_to_rotate = self.get_rotation_direction(ball)
            self.bot_rotate_and_go(dir_to_rotate)

            """
             # Holonomic TODO
             self.bot.commad(self.bot.MOVE_ANGLE + ()) etc..
            """
        else:
            self.bot.command(self.bot.STOP)

    def aiming_towards_object(self):
        # returns true if bot direction is towards ball

    # UPDATED "TICK" function 
    def updatePlan(self):
        """
        Updates the current 'mode' the robot being controlled by the planner should
        be in, based on the current situation of the world.
        """

        ball = self.world.ball

        # find out situation of robot (mode)

        # Find the different situations (states) the attacker can be in
        if self.mode == 'attacker':
            pass



        # Find the different situations (states) the defender can be in
        elif self.mode == 'defender':
            pass



        # Dog mode
        elif self.mode == 'Dog':

            if (self.state == 'noBall'):
                # implement chase
                if (not aiming_towards_object(ball)):
                    self.robotcontroller.rotate_towards_point(ball._x,ball._y)
                else: # Our robot is aiming towards the ball
                    if (not robot_in_danger_zone()):
                        distance_to_ball = self.bot.get_displacement_to_point(ball._x,ball._y)
                        danger_zone_radius = 0 # personal space of ball (ie. radius around ball)
                        self.robotcontroller.move_foward(distance_to_ball - danger_zone_radius,100) #100 = engine percentage: full throttle
                    else: # Our robot is inside dangerzone of the ball, careful now, engines on low and approach with caution
                        self.robotController.open_grabbers()
                        distance_to_ball = distance_to_ball = self.bot.get_displacement_to_point(ball._x,ball._y)
                        if (not distance_to_ball == 0):
                            self.robotcontroller.move_foward(distance_to_ball - danger_zone_radius, 25)
                        else:
                            self.robotController.close_grabbers()
                            self.state = 'hasBall'

        #FUNCTIONS TO DEFINE INSIDE planner.py:
        # aiming_towards_object(object) = TRUE if robot aims towards specified object (ie direction towards that point..)
        # robot_in_danger_zone() = TRUE if robot is inside ball's personal space
        #########
        #FUNCTIONS TO DEFINE INSIDE robotController (ie. robot.py)
        # rotate_towards_point(ball._x,ball._y) #rotates to aim towards given x,y coordinate.
        # move_foward(distance, speed) #move robot forward for given distance, at a given speed
        # open_grabbers() #duhh..
        # close_grabbers() #another duhh

        else;
            print "Error, cannot find mode"
        
