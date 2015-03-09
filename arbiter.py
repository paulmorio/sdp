from pc.models.world import WorldUpdater, World
from pc.vision import tools, calibrationgui, visiongui, camera, vision
from pc.planning.planner import Planner
from pc.robot import Robot
import cv2
import time
from pc.gui import launcher
from Tkinter import Tk


class Arbiter(object):
    """
    Ties vision/state to planning/communication.
    """

    def __init__(self, pitch, colour, our_side, profile="None",
                 video_src=0, comm_port='/dev/ttyACM0', comms=False):
        """
        Entry point for the SDP system. Initialises all components
        and runs the polling loop.

        :param pitch: Pitch number: 0 (main) 1 (secondary)
        :param colour: Our team's plate colour (blue, yellow)
        :param our_side: Our defender's side as on video feed
        :param profile: Planning profile - 'attacker', 'defender', 'dog'
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
        if profile != "None":
            self.planner = Planner(self.world, self.robot_controller, profile)
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
                model_positions, regular_positions, grabbers = \
                    self.world_updater.update_world(frame)

                # Act on the updated world model
                p_state = s_state = None
                if self.planner is not None:  # TODO tidy up the whole state drawing thing
                    self.planner.plan()
                    p_state = self.planner._state
                    s_state = self.planner._strategy.state

                fps = float(counter) / (time.clock() - timer)

                # Draw GUIs
                self.calibration_gui.show(frame, key=key)
                self.gui.draw(frame, model_positions, regular_positions,
                              grabbers, fps, self.colour, self.side, p_state,
                              s_state)

                counter += 1
                key = cv2.waitKey(1) & 0xFF  # Capture keypress
        except:
            raise
        finally:
            self.robot_controller.teardown()
            self.camera.release()
            tools.save_colors(self.pitch, self.calibration)


if __name__ == '__main__':
    # Set capture card settings
    import subprocess
    subprocess.call(['./v4lctl.sh'])

    # Create a launcher
    app = launcher.Launcher()
    app.mainloop()

    # Checks if the launcher flag was set to "launch", and if so, runs Arbiter
    if app.launching:
        arb = Arbiter(int(app.pitch.get()), app.colour.get(), app.side.get(),
                      profile=app.profile.get(), comms=app.comms.get())
        arb.run()