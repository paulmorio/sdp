class Planner():

    def __init__(self, world, mode):
        self.world = world
        self.mode = mode

    bot = None

    def _init_(self, bot):
        self.bot = bot

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
                self.dog()
            else:
                print "Error - unknown mode!"

    def attacker(self):
        pass

    def defender(self):
        pass

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
        # Get bearing
        theta = self.bot.get_rotation_to_point(self.world.ball.x, self.world.ball.y)
        # Get displacement
        displacement = self.bot.get_displacement_to_point(self.world.ball.x, self.world.ball.y)

        if displacement > 20:  # 20 is completely arbitrary, it should be a "safe" distance at which the robot can stop in front of the ball
            # Rotate-first
            if theta > 0.1:  # If the angle is greater than bearing + ~6 degrees, rotate CLKW (towards origin)
                self.bot.command(self.bot.ROTATE_RIGHT)
            elif theta < -0.1:  # If the angle is less than bearing - ~6 degrees, rotate ACLKW (away from origin)
                self.bot.command(self.bot.ROTATE_LEFT)
            else:
                self.bot.command(self.bot.MOVE_FORWARD)

            """
             # Holonomic
             self.bot.commad(self.bot.MOVE_ANGLE + ())
            """
        else:
            self.bot.command(self.bot.STOP)



