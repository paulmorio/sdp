from pc.models.world import WorldUpdater, World
from pc.vision import tools, calibrationgui, visiongui, camera, vision
from pc.planning.planner import Planner
from pc.robot import Robot
import cv2
import time
from Tkinter import *


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

    # Create launcher GUI
    gui_root = Tk()
    gui_root.resizable(width=FALSE, height=FALSE)
    gui_root.wm_title("Launcher")
    Label(gui_root, text="Group 7 SDP").grid(row=0, column=0)
    Label(gui_root, text="Test Launcher").grid(row=0, column=1)

    # Launcher controls/values for...
    # Pitch
    Label(gui_root, text="Pitch:").grid(row=1, column=0)
    pitch = StringVar(gui_root)
    pitch.set("0")  # default value
    pitch_select = OptionMenu(gui_root, pitch, "0", "1")
    pitch_select.grid(row=1, column=1)
    # Colour
    Label(gui_root, text="Colour:").grid(row=2, column=0)
    colour = StringVar(gui_root)
    colour.set("yellow")
    colour_select = OptionMenu(gui_root, colour, "yellow", "blue")
    colour_select.grid(row=2, column=1)
    # Side
    Label(gui_root, text="Side:").grid(row=3, column=0)
    side = StringVar(gui_root)
    side.set("left")
    side_select = OptionMenu(gui_root, side, "left", "right")
    side_select.grid(row=3, column=1)
    # Profile
    Label(gui_root, text="Profile:").grid(row=4, column=0)
    profile = StringVar(gui_root)
    profile.set("ms3")
    profile_select = OptionMenu(gui_root, profile, "ms3", "None")
    profile_select.grid(row=4, column=1)
    # Comms
    Label(gui_root, text="Comms:").grid(row=5, column=0)
    comms = BooleanVar(gui_root)
    comms.set(True)
    comms_select = OptionMenu(gui_root, comms, True, False)
    comms_select.grid(row=5, column=1)

    class Launcher(Frame):
        def create_widgets(self):
            self.calibrate["text"] = "Calibrate Pitch"
            self.calibrate["command"] = calibrate_table

            self.calibrate.grid(row=7, column=1)

            self.launch["text"] = "Launch"
            self.launch["command"] = self.quit

            self.launch.grid(row=7, column=0)

        def __init__(self, master=None):
            Frame.__init__(self, master)
            self.calibrate = Button(gui_root)
            self.launch = Button(gui_root)
            self.create_widgets()

    def calibrate_table():
        # TODO: this fails to close the calibration window
        from pc.vision.table_setup import TableSetup
        table_setup = TableSetup(int(pitch.get()))
        table_setup.run()

    app = Launcher(master=gui_root)
    app.mainloop()

    arb = Arbiter(int(pitch.get()), colour.get(), side.get(), profile=profile.get(), comms=comms.get())
    arb.run()