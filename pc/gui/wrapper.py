import time
from pc.vision import calibrationgui, visiongui
from Tkinter import *

CONTROLS = ["LH", "UH", "LS", "US", "LV", "UV", "LR", "UR", "LG", "UG", "LB", "UB", "CT", "BL"]

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
           "CT": 100,
           "BL": 100}


class Wrapper:
    """
    Wraps the vision and calibration GUIs into one custom GUI
    """
    def __init__(self, camera, planner, pitch, world_updater, calibration, colour, side):
        self._camera = camera
        self._planner = planner
        self._pitch = pitch
        self._world_updater = world_updater
        self._calibration = calibration
        self._colour = colour
        self._side = side

        # Initialize the main GUI
        self.root = Tk()
        self.root.resizable(width=FALSE, height=FALSE)
        self.root.wm_title("Vision Wrapper")
        self.root.bind('<Key>', self.key_press)
        # Escape to quit
        self.root.bind('<Escape>', lambda e: self.root.quit())

        # Layout
        # [Title                                 ]
        # [Vision Frame (+fps etc)][-------------]
        # [Calibration Label      ][Slider Labels]
        # [Calibration Frame      ][Sliders      ]

        # Labels
        self.title = Label(self.root, text="Group 7 - SDP - Vision GUI", height=2)
        self.title.grid(row=0, column=0, columnspan=100)
        self.calibration_label = Label(self.root, text="Calibrating: plate mask", height=2)
        self.calibration_label.grid(row=2, column=0)
        # Frames
        self.vision_frame = Label(self.root)
        self.vision_frame.grid(row=1, column=0)
        self.calibration_frame = Label(self.root)
        self.calibration_frame.grid(row=3, column=0)
        # Sliders
        self.sliders = {}
        self.slider_labels = {}
        for index, setting in enumerate(CONTROLS):
            self.sliders[setting] = Scale(self.root, from_=0, to=MAX_BAR[setting], length=300, width=10)
            self.sliders[setting].grid(row=3, column=(index+1))

            self.slider_labels[setting] = Label(self.root, text=setting)
            self.slider_labels[setting].grid(row=2, column=(index+1))

        # Used by the calibration GUI to know which mode to calibrate (plate/dot/red etc)
        self.key_event = False
        self.key = 'p'

        # The OpenCV-based calibration and vision GUIs, which get wrapped
        self.calibration_gui = calibrationgui.CalibrationGUI(self, self._calibration)
        self.gui = visiongui.VisionGUI(self, self._pitch)

        # FPS counter init
        self.counter = 1L
        self.timer = time.clock()

    def key_press(self, event):
        """
        Sets the value of self.key upon a keypress
        """
        # Raise a flag that a key_event has occurred (used by calibration to change colour mode when needed)
        self.key_event = True
        self.key = event.char

    def tick(self):
        """
        Main loop of the system. Grabs frames and passes them to the GUIs and
        the world state.
        """
        # Get frame
        frame = self._camera.get_frame()

        # Find object positions, update world model
        model_positions, regular_positions, grabbers = \
            self._world_updater.update_world(frame)

        # Act on the updated world model
        p_state = s_state = None
        if self._planner is not None:  # TODO tidy up the whole state drawing thing
            self._planner.plan()
            p_state = self._planner._state
            s_state = self._planner._strategy.state

        fps = float(self.counter) / (time.clock() - self.timer)

        # Draw GUIs
        self.calibration_gui.show(frame, self.key_event, key=self.key)
        self.gui.draw(frame, model_positions, regular_positions,
                      grabbers, fps, self._colour, self._side, p_state,
                      s_state)

        self.counter += 1

        # Reset the key_event flag
        self.key_event = False
        self.root.after(1, self.tick)

    def render(self):
        """
        The loop enabler for the GUI/program
        """
        self.tick()
        self.root.mainloop()