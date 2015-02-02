import cv2
import tools
import numpy as np

# NOTE: this file uses files:
# Callibrations (folder)
# Tools.py
# may be nice to put these in a separate location



### MAIN FUNCTION ###
class Main:
    def run(self):
        # Initial values
        pitch = 0
        video_port = 0

        # Startup vision class (responsible for all vision-related code AND draws GUI for feedback)
        vision = Vision(pitch, video_port)
        vision.init_GUI()




class Vision:

    # Vision variables
    pitch = None        # Pitch number
    video_port = None   # Port through which the video is received

    camera = None       # Camera object instance
    frame = None        # Frame received by camera
    center_point = None # Center-point of frame

    def __init__(self, pitch, video_port):
        self.pitch = pitch
        self.video_port = video_port

        # Set up camera for frames
        self.camera = Camera(port=video_port, pitch=self.pitch)
        self.frame = self.camera.get_frame()
        self.center_point = self.camera.get_adjusted_center(self.frame)

    def init_GUI(self):
        # Startup GUI
        window = GUI(self.frame)







class GUI:

    # GUI variables
    name = "Lucky Strike 7"     # GUI window name
    frame = None                # Frame received from camera
    frame_with_blank = None     # Blank (blank = BLACK, not "white") frame mask (vector filled with 0's)
    blank = None                # Blank vector transformed into matrix with given camera frame format

    def __init__(self, frame):
        self.frame = frame
        self.blank = np.zeros_like(frame)[:200, :, :]
        self.frame_with_blank = np.vstack((frame, self.blank))

        # Define popup window panel
        cv2.namedWindow(self.name)
        cv2.imshow(self.name, frame_with_blank)




class Camera:

    capture = None      # Capture socket to read frames from camera
    calibration = None  # Cropping calibration setup to specify pitch
    crop_values = None  # Specified to crop down to the pitch outline
    radial_data = None  # Radial data (?) property
    nc_matrix = None    # NEW-CAMERA radial data, stored as matrix
    c_matrix = None     # (old) camera radial data, stored as matrix
    dist = None         # radial distortion

    def __init__(self, port=0, pitch=0):
        self.capture = cv2.VideoCapture(port)
        calibration = tools.get_croppings(pitch=pitch)
        self.crop_values = tools.find_extremes(calibration['outline'])

        # Parameters used to fix radial distortion
        radial_data = tools.get_radial_data()
        self.nc_matrix = radial_data['new_camera_matrix']
        self.c_matrix = radial_data['camera_matrix']
        self.dist = radial_data['dist']

    def get_frame(self):
        status = True
        frame = self.capture.read()
        frame = self.fix_radial_distortion(frame)
        if status:
            return frame
            return frame[
                self.crop_values[2]:self.crop_values[3],
                self.crop_values[0]:self.crop_values[1]
            ]

    def fix_radial_distortion(self, frame):
        return cv2.undistort(
            frame, self.c_matrix, self.dist, None, self.nc_matrix)

    def get_adjusted_center(self, frame):
        return (320-self.crop_values[0], 240-self.crop_values[2])
        



# TODO: add no-comms option for testing
if __name__ == '__main__':
    main = Main()
    main.run()