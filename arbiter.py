from pc.models.worldmodel import WorldUpdater, World
from pc.vision import tools, calibrationgui, visiongui, camera, vision
from pc.planner import Planner
from pc.robot import Robot
import cv2
import time


class Arbiter(object):
    """
    Ties vision/state to planning/communication.
    """

    def __init__(self, pitch, colour, our_side, role=None,
                 video_src=0, comm_port='/dev/ttyACM0', comms=False):
        """
        Entry point for the SDP system. Initialises all components
        and runs the polling loop.

        :param pitch: Pitch number: 0 (main) 1 (secondary)
        :param colour: Our team's plate colour (blue, yellow)
        :param our_side: Our defender's side as on video feed
        :param role: Planning role - 'attacker', 'defender', 'dog'
        :param video_src: Source of feed - 0 default for DICE cameras
        :param comm_port: Robot serial port
        :param comms: Enable serial communication
        :return:
        """

        assert pitch in [0, 1]
        assert colour in ['yellow', 'blue']
        assert our_side in ['left', 'right']

        self.pitch = pitch
        self.colour = colour
        self.side = our_side
        self.calibration = tools.get_colors(pitch)

        # Set up capture device
        self.camera = camera.Camera(pitch, video_src=video_src)

        # Set up vision - note that this discards the colour-corrupt first frame
        frame_shape = self.camera.get_frame().shape
        frame_center = self.camera.get_adjusted_center()
        self.vision = vision.Vision(pitch, colour, our_side, frame_shape,
                                    frame_center, self.calibration,
                                    perspective_correction=True)

        # Set up world model
        self.world = World(self.side, self.pitch)
        self.world_updater = WorldUpdater(self.pitch, self.colour, self.side,
                                          self.world, self.vision)

        # Set up robotController
        self.robot_controller = Robot(port=comm_port, comms=comms)

        # Set up the planner
        if role is not None:
            assert(role in ['defender', 'attacker', 'dog'])
            mode = role
            self.planner = Planner(self.world, self.robot_controller, mode)
        else:
            self.planner = None

        # Set up GUI
        self.gui = visiongui.VisionGUI(self.pitch)
        self.calibration_gui = calibrationgui.CalibrationGUI(self.calibration)

    def run(self):
        """
        Main loop of the system. Grabs frames and passes them to the GUIs and
        the world state.
        Also captures keys for exit (escape) and for the calibration gui.
        """
        counter = 1L
        timer = time.clock()

        key = True
        try:
            while key != 27:  # escape to quit
                # Get frame
                frame = self.camera.get_frame()

                # Find object positions, update world model
                model_positions, regular_positions, grabber_positions = \
                    self.world_updater.update_world(frame)

                # Act on the updated world model
                if self.planner is not None:
                    self.planner.update_plan()

                fps = float(counter) / (time.clock() - timer)

                # Draw GUIs
                self.calibration_gui.show(frame, key=key)
                self.gui.draw(
                    frame, model_positions, regular_positions,
                    grabber_positions, fps, self.colour, self.side)

                counter += 1
                key = cv2.waitKey(1) & 0xFF  # Capture keypress
        except:
            raise
        finally:
            self.robot_controller.close()
            self.camera.release()
            tools.save_colors(self.pitch, self.calibration)


# TODO add comm_port and video source arguments - defaults are fine though.
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "pitch", help="[0] Main pitch, [1] Secondary pitch"
    )
    parser.add_argument(
        "colour", help="The colour of our team - ['yellow', 'blue'] allowed."
    )
    parser.add_argument(
        "side", help="The side of our defender ['left', 'right'] allowed."
    )
    parser.add_argument(
        "role", help="The robot's role - ['defender', 'attacker', 'dog']"
    )
    parser.add_argument(
        "-t", "--tablesetup",
        help="Bring up the table setup window",
        action="store_true"
    )
    parser.add_mutually_exclusive_group()
    parser.add_argument(
        "-v", "--visiononly",
        help="Run the vision system without the planner or robot/comms",
        action="store_true"
    )
    parser.add_argument(
        "-n", "--nocomms",
        help="Run without comms.",
        action="store_true"
    )

    args = parser.parse_args()
    assert(int(args.pitch) in [0, 1])
    assert(args.colour in ["blue", "yellow"])
    assert(args.side in ["left", "right"])

    if args.tablesetup:
        from pc.vision.table_setup import TableSetup
        tablesetup = TableSetup(int(args.pitch))
        tablesetup.run()

    if args.visiononly:
        arb = Arbiter(int(args.pitch), args.colour, args.side,
                      role=None, comms=False)
    elif args.nocomms:
        assert args.role in ['defender', 'attacker', 'dog']
        arb = Arbiter(int(args.pitch), args.colour, args.side,
                      role=args.role, comms=False)

    else:
        assert args.role in ['defender', 'attacker']
        arb = Arbiter(int(args.pitch), args.colour, args.side,
                      role=args.role, comms=True)
    arb.run()