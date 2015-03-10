import cv2
import numpy as np
#from pc.gui.wrapper import CONTROLS # TODO: no bueno?
from PIL import Image, ImageTk

KEYS = {'y': 'yellow',
        'r': 'red',
        'b': 'blue',
        'd': 'dot',
        'p': 'plate'}

CONTROLS = ["LH", "UH", "LS", "US", "LV", "UV", "LR", "UR", "LG", "UG", "LB", "UB", "CT", "BL"]


class CalibrationGUI(object):

    def __init__(self, calibration_label_wrapper, calibration_frame_wrapper, sliders, calibration):
        self.color = 'plate'
        self.calibration_frame_wrapper = calibration_frame_wrapper
        self.sliders = sliders
        self.calibration_label_wrapper = calibration_label_wrapper
        self.calibration = calibration
        self.set_window()

    def set_window(self):
        # Hue
        self.sliders['LH'].set(self.calibration[self.color]['hsv_min'][0])
        self.sliders['UH'].set(self.calibration[self.color]['hsv_max'][0])

        # Saturation
        self.sliders['LS'].set(self.calibration[self.color]['hsv_min'][1])
        self.sliders['US'].set(self.calibration[self.color]['hsv_max'][1])

        # Value
        self.sliders['LV'].set(self.calibration[self.color]['hsv_min'][2])
        self.sliders['UV'].set(self.calibration[self.color]['hsv_max'][2])

        # Red
        self.sliders['LR'].set(self.calibration[self.color]['rgb_min'][0])
        self.sliders['UR'].set(self.calibration[self.color]['rgb_max'][0])

        # Green
        self.sliders['LG'].set(self.calibration[self.color]['rgb_min'][1])
        self.sliders['UG'].set(self.calibration[self.color]['rgb_max'][1])

        # Blue
        self.sliders['LB'].set(self.calibration[self.color]['rgb_min'][2])
        self.sliders['UB'].set(self.calibration[self.color]['rgb_max'][2])

        # Contrast/blur
        self.sliders['CT'].set(self.calibration[self.color]['contrast'])
        self.sliders['BL'].set(self.calibration[self.color]['blur'])

    def change_color(self, color):
        self.calibration_label_wrapper.configure(text="Calibrating "+self.color+" mask")
        self.color = color
        self.set_window()

    def show(self, frame, key_event, key=None):
        if key_event:
            try:
                self.change_color(KEYS[key])
            except:
                pass

        get_trackbar_pos = lambda val: self.sliders[val].get()

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

        # Convert the image to Tkinter format, and display
        img = Image.fromarray(cv2.cvtColor(mask, cv2.COLOR_GRAY2RGBA))
        img_tk = ImageTk.PhotoImage(image=img)
        self.calibration_frame_wrapper.img_tk = img_tk
        self.calibration_frame_wrapper.configure(image=img_tk)

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
