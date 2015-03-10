from Tkinter import *
import time
from pc.vision import calibrationgui, visiongui

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

        self.root = Tk()
        self.root.resizable(width=FALSE, height=FALSE)
        self.root.wm_title("Wrapper Test")
        self.root.bind('<Key>', self.key_press)
        self.root.bind('<Escape>', lambda e: self.root.quit())

        # [Title                                       ]
        # [Vision Frame (+fps etc)][-------------------]
        # [Calibration Frame Label][-------------------]
        # [Calibration Frame      ][Calibration Sliders]
        # Labels
        self.vision_label = Label(self.root, text="Group 7 - SDP - GUI Test")
        self.vision_label.grid(row=0, column=0, columnspan=5)
        self.calibration_label = Label(self.root, text="Calibrating: plate mask")
        self.calibration_label.grid(row=2, column=0)
        # Frames
        self.vision_frame = Label(self.root)
        self.vision_frame.grid(row=1, column=0)
        self.calibration_frame = Label(self.root)
        self.calibration_frame.grid(row=3, column=0)
        # Sliders
        self.sliders = {}
        for index, setting in enumerate(CONTROLS):
            self.sliders[setting] = Scale(self.root, from_=0, to=MAX_BAR[setting], label=setting)
            self.sliders[setting].grid(row=3, column=(index+1))

        self.key = 'p'

        self._calibration_gui = calibrationgui.CalibrationGUI(self, self._calibration)
        self._gui = visiongui.VisionGUI(self, self._pitch)

    def key_press(self, event):
        """
        Sets the value of self.key upon a keypress

        :return:
        """
        self.key = event.char

    def tick(self):

        counter = 1L
        timer = time.clock()

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

        fps = float(counter) / (time.clock() - timer)

        self.vision_frame.configure(text="FPS: "+'%.2f' % fps)

        # Draw GUIs
        self._calibration_gui.show(frame, key=self.key)
        self._gui.draw(frame, model_positions, regular_positions,
                       grabbers, fps, self._colour, self._side, p_state,
                       s_state)

        counter += 1
        self.root.after(1, self.tick)

    def render(self):
        self.tick()
        self.root.mainloop()