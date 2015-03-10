import cv2
import numpy as np
#from pc.gui.wrapper import CONTROLS
from PIL import Image, ImageTk

KEYS = {'y': 'yellow',
        'r': 'red',
        'b': 'blue',
        'd': 'dot',
        'p': 'plate'}

CONTROLS = ["LH", "UH", "LS", "US", "LV", "UV", "LR", "UR", "LG", "UG", "LB", "UB", "CT", "BL"]


class CalibrationGUI(object):

    def __init__(self, wrapper, calibration):
        self.color = 'plate'
        self.wrapper = wrapper
        self.calibration = calibration
        self.set_window()

    def set_window(self):
        # Hue
        self.wrapper.sliders['LH'].set(self.calibration[self.color]['hsv_min'][0])
        self.wrapper.sliders['UH'].set(self.calibration[self.color]['hsv_max'][0])

        # Saturation
        self.wrapper.sliders['LS'].set(self.calibration[self.color]['hsv_min'][1])
        self.wrapper.sliders['US'].set(self.calibration[self.color]['hsv_max'][1])

        # Value
        self.wrapper.sliders['LV'].set(self.calibration[self.color]['hsv_min'][2])
        self.wrapper.sliders['UV'].set(self.calibration[self.color]['hsv_max'][2])

        # Red
        self.wrapper.sliders['LR'].set(self.calibration[self.color]['rgb_min'][0])
        self.wrapper.sliders['UR'].set(self.calibration[self.color]['rgb_max'][0])

        # Green
        self.wrapper.sliders['LG'].set(self.calibration[self.color]['rgb_min'][1])
        self.wrapper.sliders['UG'].set(self.calibration[self.color]['rgb_max'][1])

        # Blue
        self.wrapper.sliders['LB'].set(self.calibration[self.color]['rgb_min'][2])
        self.wrapper.sliders['UB'].set(self.calibration[self.color]['rgb_max'][2])

        # Contrast/blur
        self.wrapper.sliders['CT'].set(self.calibration[self.color]['contrast'])
        self.wrapper.sliders['BL'].set(self.calibration[self.color]['blur'])

    def change_color(self, color):
        self.wrapper.calibration_label.configure(text="Calibrating "+self.color+" mask")
        self.color = color
        self.set_window()

    def show(self, frame, key=None):
        try:
            self.change_color(KEYS[key])
        except:
            pass

        get_trackbar_pos = lambda val: self.wrapper.sliders[val].get()

        values = {}
        for setting in CONTROLS:
            values[setting] = float(get_trackbar_pos(setting))
        values['BL'] = int(values['BL'])

        self.calibration[self.color]['hsv_min'] = \
            np.array([values['LH'], values['LS'], values['LV']])
        self.calibration[self.color]['hsv_max'] = \
            np.array([values['UH'], values['US'], values['UV']])

        self.calibration[self.color]['rgb_min'] = \
            np.array([values['LR'], values['LG'], values['LB']])
        self.calibration[self.color]['rgb_max'] = \
            np.array([values['UR'], values['UG'], values['UB']])

        self.calibration[self.color]['contrast'] = values['CT']
        self.calibration[self.color]['blur'] = values['BL']

        mask = self.get_mask(frame)

        # If the image is not just a blank array
        if np.any(mask):
            # Convert the image to Tkinter format, and display
            cv2img = cv2.cvtColor(mask, cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2img)
            img_tk = ImageTk.PhotoImage(image=img)
            self.wrapper.root.calibration_frame.configure(image=img_tk)

    # Duplicated from tracker.py
    def get_mask(self, frame):
        blur = self.calibration[self.color]['blur']
        if blur > 1:
            frame = cv2.blur(frame, (blur, blur))

        contrast = self.calibration[self.color]['contrast']
        if contrast > 1.0:
            frame = cv2.add(frame, np.array([contrast]))

        frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        min_hsv_color = self.calibration[self.color]['hsv_min']
        max_hsv_color = self.calibration[self.color]['hsv_max']
        hsv_frame_mask = cv2.inRange(frame_hsv, min_hsv_color, max_hsv_color)

        min_rgb_color = self.calibration[self.color]['rgb_min']
        max_rgb_color = self.calibration[self.color]['rgb_max']
        rgb_frame_mask = cv2.inRange(frame, min_rgb_color, max_rgb_color)

        frame_mask = cv2.bitwise_and(hsv_frame_mask, hsv_frame_mask, mask=rgb_frame_mask)

        return frame_mask


# Dummy cv trackbar call function
def nothing(x):
    pass
