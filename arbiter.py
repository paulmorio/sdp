from pc.robot import Robot
from pc.models.worldmodel import WorldUpdater, World
from pc.vision import tools, calibrationgui, visiongui
import cv2
import time


class Arbiter(object):
    """
    Ties vision/state to planning/communication.
    """

    def __init__(self, pitch, colour, our_side,
                 comm_port='/dev/ttyACM0', comms=0):
        """
        Entry point for the SDP system.
        Params:
            [int] pitch         Pitch number: 0 (main) 1 (secondary)
            [string] color      Team colour: 'blue' or 'yellow'
            [string] our_side   Team side: 'left' or 'right' as on feed
            [string] comm_port  Robot serial comm port
            [int] comms         Enable (1) or disable (0) comms
        """
        assert pitch in [0, 1]
        assert colour in ['yellow', 'blue']
        assert our_side in ['left', 'right']

        self.pitch = pitch
        self.colour = colour
        self.side = our_side
        self.robot = Robot(port=comm_port) if comms == 1 else None

        self.world = World(self.side, self.pitch)
        self.world_updater = WorldUpdater(self.pitch, self.colour,
                                          self.side, self.world)
        self.calibration = tools.get_colors(pitch)

        # TODO Set up planner

        # Set up GUI
        self.gui = visiongui.VisionGUI(self.pitch)
        self.calibration_gui = calibrationgui.CalibrationGUI(self.calibration)

    def run(self):
        """
            Dragons are slain. Sort of.
        """
        counter = 1L
        timer = time.clock()

        key = True
        try:
            while key != 27:  # escape to quit

                # Find object positions, update world model
                frame, model_positions, regular_positions = \
                    self.world_updater.update_world()
                fps = float(counter) / (time.clock() - timer)

                # Draw GUIs
                self.calibration_gui.show(frame['frame'], key=key)
                self.gui.draw(
                    frame['frame'], model_positions, regular_positions, fps,
                    our_color=self.colour, our_side=self.side, key=key)

                counter += 1
                key = cv2.waitKey(1) & 0xFF  # Capture keypress
        except:
            # TODO Close serial connection, etc (via planner)
            raise
        finally:
            # Save calibrations
            tools.save_colors(self.pitch, self.calibration)
            # Close serial connection


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("pitch", help="[0] Main pitch, [1] Secondary pitch")
    parser.add_argument(
        "side", help="The side of our defender ['left', 'right'] allowed."
    )
    parser.add_argument(
        "colour", help="The colour of our team - ['yellow', 'blue'] allowed."
    )
    parser.add_argument(
        "-t", "--tablesetup",
        help="Brings up the table setup window",
        action="store_true"
    )

    args = parser.parse_args()

    assert(int(args.pitch) in [0,1])
    assert(args.colour in ["blue", "yellow"])
    assert(args.side in ["left", "right"])

    if args.tablesetup:
        from pc.vision.table_setup import TableSetup
        tablesetup = TableSetup(int(args.pitch))
        tablesetup.run()

    arb = Arbiter(int(args.pitch), args.colour, args.side)
    arb.run()