from ..vision.vision import Vision
from ..vision.camera import Camera
from ..vision.tools import get_colors
from postprocessing import Postprocessing
from models import *
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)


class World(object):
    """
    This class describes the environment
    """

    def __init__(self, our_side, pitch_num):
        assert our_side in ['left', 'right']
        self._pitch = Pitch(pitch_num)
        self._our_side = our_side
        self._their_side = 'left' if our_side == 'right' else 'right'
        self._ball = Ball(0, 0, 0, 0)
        self._robots = []
        self._robots.append(Robot(0, 0, 0, 0, 0))
        self._robots.append(Robot(1, 0, 0, 0, 0))
        self._robots.append(Robot(2, 0, 0, 0, 0))
        self._robots.append(Robot(3, 0, 0, 0, 0))
        self._goals = []
        self._goals.append(Goal(0, 0, self._pitch.height/2.0, 0))
        self._goals.append(Goal(3, self._pitch.width, self._pitch.height/2.0, pi))

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


class WorldUpdater:
    """
    Process camera feed and update the world model.
    """

    def __init__(self, pitch, colour, our_side, world, pre_options=None):
        """
        Params:
            [int] pitch       0 - main pitch, 1 - secondary pitch
            [string] colour   our team  colour - 'red' or 'yellow'
            [string] our_side the side we're on - 'left' or 'right'
        """
        assert pitch in [0, 1]
        assert colour in ['yellow', 'blue']
        assert our_side in ['left', 'right']

        self.pitch = pitch
        self.pre_options = pre_options
        self.colour = colour
        self.side = our_side
        self.world = world

        # Set up camera for frames
        self.camera = Camera(pitch=self.pitch, options=pre_options)
        frame = self.camera.get_frame()['frame']
        center_point = self.camera.get_adjusted_center()

        # Set up vision
        self.calibration = get_colors(pitch)
        self.vision = Vision(
            pitch=pitch, colour=colour, our_side=our_side,
            frame_shape=frame.shape, frame_center=center_point,
            calibration=self.calibration)

        self.postprocessing = Postprocessing()

    def update_world(self):
        """
        Read a frame and update the world model appropriately.
        Returns the positions for drawing on the UI feed.
        """
        frame = self.camera.get_frame()
        # Find object positions - model_positions have their y coordinate inverted
        model_positions, regular_positions = self.vision.locate(frame['frame'])
        model_positions = self.postprocessing.analyze(model_positions)

        self.world.update_positions(model_positions)

        return frame, model_positions, regular_positions  # For drawing on GUI