from pc.models.world import WorldUpdater, World
from pc.vision import tools, camera, vision
from pc.planning.planner import Planner
from pc.robot import Robot
from pc.gui import launcher, wrapper


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
        self.gui_wrapper = wrapper.Wrapper(self.camera, self.planner, self.pitch, self.world_updater,
                                           self.calibration, self.colour, self.side)

    def run(self):
        """
        Creates a GUI wrapper for the vision system, cleanly exits when finished.
        """

        try:
            self.gui_wrapper.render()
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