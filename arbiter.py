from pc.models.world import WorldUpdater, World
from pc.vision import tools, camera, vision
from pc.planning.planner import Planner
from pc.robot import Robot
import time
from pc.vision import calibrationgui, visiongui
from Tkinter import *
from pc.vision.vision import split_into_rgb_channels
import cv2

CONTROLS = ["LH", "UH", "LS", "US", "LV", "UV", "LR",
            "UR", "LG", "UG", "LB", "UB", "BR", "BL",
            "C1", "C2"]

MAX_BAR = {"LH": 360,
           "UH": 360,
           "LS": 255,
           "US": 255,
           "LV": 255,
           "UV": 255,
           "LR": 255,
           "UR": 255,
           "LG": 255,
           "UG": 255,
           "LB": 255,
           "UB": 255,
           "BR": 100,
           "BL": 100,
           "C1": 100,
           "C2": 100}


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
        assert profile in ['ms3', 'attacker', 'penalty', 'None']

        self.pitch = pitch
        self.colour = colour
        self.side = our_side
        self.profile = profile
        self.calibration = tools.get_colors(pitch)
        self.comms = comms

        self.contrast_toggle = False
        self.vision_filter_toggle = False

        # Set up capture device
        self.camera = camera.Camera(pitch, video_src=video_src)

        # Set up robotController
        self.robot_controller = Robot(port=comm_port, comms=comms)

        # Set up vision
        self.vision = None
        self.start_vision()

        # Set up world model; updater
        self.world = None
        self.world_updater = None
        self.start_world()

        # Set up the planner
        self.planner = None
        self.start_planner()

        # Initialize the main GUI
        self.root = Tk()
        self.root.resizable(width=FALSE, height=FALSE)
        self.root.wm_title("Vision Wrapper")
        self.root.bind('<Key>', self.key_press)
        # Overwrite the "any key" bind with other, more specific binds
        self.root.bind('<Escape>', lambda e: self.root.quit())  # Escape to quit
        self.root.bind('<q>', lambda e: self.root.quit())  # Q to |q|uit
        self.root.bind('<c>', lambda e: self.switch_colours())  # C to switch |c|olours
        self.root.bind('<s>', lambda e: self.switch_sides())  # S to switch |s|ides
        self.root.bind('<l>', lambda e: self.toggle_planning())  # L to toggle p|l|anning
        self.root.bind('<a>', lambda e: self.clear_calibrations())  # A to reset current c|a|libration
        self.root.bind('<e>', lambda e: self.take_penalty())  # E to take a p|e|nalty
        self.root.bind('<o>', lambda e: self.toggle_contrast())  # O to toggle c|o|ntrast

        # GUI Layout
        # [Title                                 ]
        # [Vision Frame (+fps etc)][Buttons      ]
        # [Calibration Label      ][Slider Labels]
        # [Calibration Frame      ][Sliders      ]

        vision_height = 16  # The height of the vision frame in TKinter grid terms - allows for button spacing

        # Labels
        self.title = Label(self.root, text="Group 7 - SDP - Vision GUI",
                           height=2)
        self.title.grid(row=0, column=0, columnspan=100)
        self.calibration_label = \
            Label(self.root, text="Calibrating: plate mask", height=2)
        self.calibration_label.grid(row=(vision_height+2), column=0)
        # Frames
        self.vision_frame = Label(self.root)
        self.vision_frame.grid(row=1, column=0, rowspan=vision_height)
        self.calibration_frame = Label(self.root)
        self.calibration_frame.grid(row=(vision_height+3), column=0)
        # Sliders
        self.sliders = {}
        self.slider_labels = {}
        for index, setting in enumerate(CONTROLS):
            self.sliders[setting] = Scale(self.root, from_=0,
                                          to=MAX_BAR[setting],
                                          length=300, width=10)
            self.sliders[setting].grid(row=(vision_height+3), column=(index+1))

            self.slider_labels[setting] = Label(self.root, text=setting)
            self.slider_labels[setting].grid(row=(vision_height+2), column=(index+1))

        # Buttons
        # Planning pause/resume toggle
        self.planner_paused = False  # Flag for pausing/resuming the planning
        planning_toggle = Button(self.root)
        planning_toggle["text"] = "P[l]anning Toggle"
        planning_toggle["command"] = self.toggle_planning
        planning_toggle.grid(row=1, column=1, columnspan=5)
        # Calibration reset
        calib_reset = Button(self.root)
        calib_reset["text"] = "Reset Current\nC[a]libration"
        calib_reset["command"] = self.clear_calibrations
        calib_reset.grid(row=2, column=1, columnspan=5)
        # Side switch
        side_switch = Button(self.root)
        side_switch["text"] = "Switch [S]ides"
        side_switch["command"] = self.switch_sides
        side_switch.grid(row=3, column=1, columnspan=5)
        # Colour switch
        colour_switch = Button(self.root)
        colour_switch["text"] = "Switch [C]olours"
        colour_switch["command"] = self.switch_colours
        colour_switch.grid(row=4, column=1, columnspan=5)
        # Penalty mode
        penalty_mode = Button(self.root)
        penalty_mode["text"] = "Take P[e]nalty"
        penalty_mode["command"] = self.take_penalty
        penalty_mode.grid(row=5, column=1, columnspan=5)
        # Vision filter toggle
        vision_filter_toggle = Button(self.root)
        vision_filter_toggle["text"] = "Toggle Vision\nFilters (-FPS)"
        vision_filter_toggle["command"] = self.toggle_vision_filters
        vision_filter_toggle.grid(row=7, column=1, columnspan=5)
        # Contrast toggle
        contrast_toggle = Button(self.root)
        contrast_toggle["text"] = "Toggle C[o]ntrast\nEXPERIMENTAL (-FPS)"
        contrast_toggle["command"] = self.toggle_contrast
        contrast_toggle.grid(row=8, column=1, columnspan=5)

        # Used by the calibration GUI to know
        # which mode to calibrate (plate/dot/red etc)
        self.key_event = False
        self.key = 'p'

        # The OpenCV-based calibration and vision GUIs, which get wrapped
        self.calibration_gui = calibrationgui.CalibrationGUI(self, self.calibration)
        self.gui = visiongui.VisionGUI(self, self.pitch, self.contrast_toggle)

        # FPS counter init
        self.counter = 1L
        self.timer = time.clock()

    def start_planner(self):
        """
        Starts a new planner depending on our current world state, robot controller, and profile.
        """
        if self.profile != "None":
            self.planner = Planner(self.world, self.robot_controller, self.profile)
        else:
            self.planner = None

    def start_vision(self):
        """
        Start a new vision system - note that this discards the colour-corrupt first frame.
        """
        frame_shape = self.camera.get_frame().shape
        frame_center = self.camera.get_adjusted_center()
        self.vision = vision.Vision(self.pitch, self.colour, self.side, frame_shape,
                                    frame_center, self.calibration,
                                    perspective_correction=True)

    def start_world(self):
        """
        Starts a new world model and world updater.
        """
        self.world = World(self.side, self.pitch)
        self.world_updater = WorldUpdater(self.pitch, self.colour, self.side,
                                          self.world, self.vision)

    def key_press(self, event):
        """
        Sets the value of self.key upon a keypress.
        """
        # Raise a flag that a key_event has occurred (used by
        # calibration to change colour mode when needed)
        self.key_event = True
        self.key = event.char

    def toggle_planning(self):
        """
        Toggles planning to prevent updates.
        """
        self.planner.robot_ctl.stop()
        self.planner_paused = not self.planner_paused

    def clear_calibrations(self):
        """
        Resets the calibration sliders.
        If the slider is a "lower" slider, sets the value to 0;
        if the slider is an "upper" slider, sets the value to max;
        if the slider is brightness/blur, sets the value to 0.
        """
        # Hue
        self.sliders['LH'].set(0)
        self.sliders['UH'].set(MAX_BAR['UH'])

        # Saturation
        self.sliders['LS'].set(0)
        self.sliders['US'].set(MAX_BAR['US'])

        # Value
        self.sliders['LV'].set(0)
        self.sliders['UV'].set(MAX_BAR['UV'])

        # Red
        self.sliders['LR'].set(0)
        self.sliders['UR'].set(MAX_BAR['UR'])

        # Green
        self.sliders['LG'].set(0)
        self.sliders['UG'].set(MAX_BAR['UG'])

        # Blue
        self.sliders['LB'].set(0)
        self.sliders['UB'].set(MAX_BAR['UB'])

        # Brightness/blur
        self.sliders['BR'].set(0)
        self.sliders['BL'].set(0)

    def switch_sides(self):
        """
        Switch which side we're on.
        """
        our_new_side = ""
        if self.side == "left":
            our_new_side = "right"
        elif self.side == "right":
            our_new_side = "left"

        self.side = our_new_side

        # Restart the vision system, world model + updater, and planner
        self.start_vision()
        self.start_world()
        self.start_planner()

    def switch_colours(self):
        """
        Switch which colour we are.
        """
        our_new_colour = ""
        if self.colour == "blue":
            our_new_colour = "yellow"
        elif self.colour == "yellow":
            our_new_colour = "blue"

        self.colour = our_new_colour

        # Restart the vision system, world model + updater, and planner
        self.start_vision()
        self.start_world()
        self.start_planner()

    def take_penalty(self):
        """
        Set the profile to penalty, and restart the planner
        Planning automatically resumes to "attacker" when the penalty has been taken.
        """
        self.profile = 'penalty'
        self.start_planner()

    def toggle_contrast(self):
        """
        Toggle the contrast filtering on vision.
        Restarts the vision system, and the vision GUI.
        """
        self.contrast_toggle = not self.contrast_toggle
        self.start_vision()
        self.gui = visiongui.VisionGUI(self, self.pitch, self.vision_filter_toggle)

    def toggle_vision_filters(self):
        """
        Toggle whether or not the "misc" sliders are affecting the GUI view of the pitch.
        Restarts the vision GUI.
        """
        self.vision_filter_toggle = not self.vision_filter_toggle
        self.gui = visiongui.VisionGUI(self, self.pitch, self.vision_filter_toggle)

    def run(self):
        """
        Ticks the whole system, cleanly exits saving calibrations and resetting the robot.
        """
        try:
            self.tick()
            self.root.mainloop()
        except:
            raise
        finally:
            if self.comms:
                self.robot_controller.teardown()
            self.camera.release()
            tools.save_colors(self.pitch, self.calibration)

    def tick(self):
        """
        Main loop of the system. Grabs frames and passes them to the GUIs and
        the world state.
        """
        # Get frame
        frame = self.camera.get_frame()

        ct_clipLimit = self.sliders['C1'].get()
        ct_tileGridSize = self.sliders['C2'].get()
        if self.contrast_toggle:
            # Apply contrast changes first
            r, g, b = split_into_rgb_channels(frame)

            if ct_clipLimit == 0:
                ct_clipLimit += 1

            if ct_tileGridSize == 0:
                ct_tileGridSize += 1

            clahe = cv2.createCLAHE(clipLimit=1.0*ct_clipLimit,
                                    tileGridSize=(1.0*ct_tileGridSize, 1.0*ct_tileGridSize))

            r_c = clahe.apply(r)
            g_c = clahe.apply(g)
            b_c = clahe.apply(b)

            frame = cv2.merge((r_c, g_c, b_c))

        # Find object positions, update world model
        model_positions, regular_positions, grabbers = \
            self.world_updater.update_world(frame)

        # Act on the updated world model
        p_state = s_state = None
        if self.planner is not None:
            if not self.planner_paused:
                self.planner.plan()
                p_state = self.planner.planner_state_string
                s_state = self.planner.strategy_state_string

        fps = float(self.counter) / (time.clock() - self.timer)

        # Draw GUIs
        self.calibration_gui.show(frame, self.key_event, key=self.key)
        self.gui.draw(frame, model_positions, regular_positions,
                      grabbers, fps, self.colour, self.side, p_state,
                      s_state, self.sliders['BR'].get(), self.sliders['BL'].get())

        self.counter += 1

        # Reset the key_event flag
        self.key_event = False
        self.root.after(1, self.tick)  # TODO Oh wow.


if __name__ == '__main__':
    # Set capture card settings
    import subprocess
    subprocess.call(['./v4lctl.sh'])

    # Create a launcher
    from pc.gui import launcher
    app = launcher.Launcher()
    app.mainloop()

    # Checks if the launcher flag was set to "launch", and if so, runs Arbiter
    if app.launching:
        arb = Arbiter(int(app.pitch.get()), app.colour.get(), app.side.get(),
                      profile=app.profile.get(), comms=app.comms.get())
        arb.run()