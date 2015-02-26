from postprocessing import Postprocessing
from models import *
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)


class World(object):
    """
    Describe the pitch environment.
    """

    def __init__(self, our_side, pitch_num):
        assert our_side in ['left', 'right']
        self._pitch = Pitch(pitch_num)
        self._our_side = our_side
        self._their_side = 'left' if our_side == 'right' else 'right'
        self._ball = Ball(0, 0, 0, 0)

        self._robots = [
            Robot(0, 0, 0, 0, 0), Robot(1, 0, 0, 0, 0),
            Robot(2, 0, 0, 0, 0), Robot(3, 0, 0, 0, 0)
        ]
        self._goals = [
            Goal(0, 0, self._pitch.height/2.0, 0),  # Leftmost, facing angle 0
            Goal(3, self._pitch.width, self._pitch.height/2.0, pi)  # Rightmost
        ]
        # Grabber areas - TODO should be adjusted once the robot is finalised
        self.our_defender.catcher_area = \
            {'width': 30, 'height': 25, 'front_offset': 10}  # In pixels???
        self.our_attacker.catcher_area = \
            {'width': 30, 'height': 25, 'front_offset': 10}
        self.grabbers = {'our_defender': self.our_defender.catcher_area,
                         'our_attacker': self.our_attacker.catcher_area}

    @property
    def our_attacker(self):
        return self._robots[2] if self._our_side == 'left' else self._robots[1]

    @property
    def their_attacker(self):
        return self._robots[1] if self._our_side == 'left' else self._robots[2]

    @property
    def our_defender(self):
        return self._robots[0] if self._our_side == 'left' else self._robots[3]

    @property
    def their_defender(self):
        return self._robots[3] if self._our_side == 'left' else self._robots[0]

    @property
    def ball(self):
        return self._ball

    @property
    def our_goal(self):
        return self._goals[0] if self._our_side == 'left' else self._goals[1]

    @property
    def their_goal(self):
        return self._goals[1] if self._our_side == 'left' else self._goals[0]

    @property
    def pitch(self):
        return self._pitch

    def update_positions(self, pos_dict):
        """
            This method will update the positions of the pitch objects
            that it gets passed by the vision system
        """
        self.our_attacker.vector = pos_dict['our_attacker']
        self.their_attacker.vector = pos_dict['their_attacker']
        self.our_defender.vector = pos_dict['our_defender']
        self.their_defender.vector = pos_dict['their_defender']
        self.ball.vector = pos_dict['ball']

        # Checking if the robot locations make sense:
        # Is the side correct:
        if (self._our_side == 'left' and
                not(self.our_defender.x < self.their_attacker.x
                    < self.our_attacker.x < self.their_defender.x)):
            print "WARNING: The sides are probably wrong!"

        if (self._our_side == 'right' and
                not(self.our_defender.x > self.their_attacker.x
                    > self.our_attacker.x > self.their_defender.x)):
            print "WARNING: The sides are probably wrong!"

    def ball_in_area(self, robots):
        """
        Return True if the ball is in the given robots' area
        :param robots: list of robot models corresponding to the queried zones
        """
        for robot in robots:
            if self.pitch.zones[robot.zone].isInside(self.ball.x, self.ball.y):
                return True
        return False

    def ball_in_play(self):
        """
        Return True if the ball is in play (the ball is in one of the four
        margins.
        :return boolean: True if ball is in play, else False.
        """
        return self.ball_in_area(self._robots)


class WorldUpdater:
    """
    Ties vision to the world model.
    Process camera feed and update the world model.
    """

    def __init__(self, pitch, colour, our_side, world, vision):
        """
        Params:
            [int] pitch       0 - main pitch, 1 - secondary pitch
            [string] colour   our team  colour - 'blue' or 'yellow'
            [string] our_side the side we're on - 'left' or 'right'

        """
        assert pitch in [0, 1]
        assert colour in ['yellow', 'blue']
        assert our_side in ['left', 'right']

        self.pitch = pitch
        self.colour = colour
        self.side = our_side
        self.world = world
        self.vision = vision
        self.postprocessing = Postprocessing()

    def update_world(self, frame):
        """
        Read a frame and update the world model appropriately.
        Returns the object positions for drawing on the UI feed.
        """
        # Find object positions, return for gui drawing
        model_positions, regular_positions = self.vision.locate(frame)
        model_positions = self.postprocessing.analyze(model_positions)
        self.world.update_positions(model_positions)
        return model_positions, regular_positions
