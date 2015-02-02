import cv2
import tools
import numpy as np
from threading import Thread

# NOTE: this file uses files:
# Callibrations (folder)
# Tools.py
# may be nice to put these in a separate location



### MAIN FUNCTION ###
class Main:
    def run(self):
        # Initial values
        tableNumber = 0
        video_port = 0
        name = "Lucky Strike 7" # Name of the main GUI frame

        # Startup vision class (responsible for all vision-related code AND draws GUI for feedback)
        vision = Vision(tableNumber, video_port, name)



# SOFTWARE BEHIND WHAT THE CAMERA RECEIVES
class Vision:

    # Vision variables
    camera = None       # Camera object instance
    frame = None        # Frame received by camera
    center_point = None # Center-point of frame

    def __init__(self, tableNumber, video_port, name):

        # Set up camera for capturing frames
        self.camera = Camera(tableNumber, video_port)
        self.camera.start()

        # Set up GUI for displaying what's going on
        self.gui = GUI(name, self.camera)
        self.gui.start()





# CAMERA CLASS (single object), RESPONSIBLE FOR CAPTURING FRAMES
class Camera(Thread):
    
    capture = None      # capture socket to receive frames from the camera
    frame = None        # most recent frame from camera

    # Frame configurations
    crop_values = None  # Specified to crop down to the tableNumber outline
    nc_matrix = None    # NEW-CAMERA radial data, stored as matrix
    c_matrix = None     # (old) camera radial data, stored as matrix
    dist = None         # radial distortion

    def __init__(self, tableNumber, video_port):
        super(Camera,self).__init__()

        self.capture = cv2.VideoCapture(0)

        # Parameters used to crop frame to only contain the table in view
        calibration = tools.get_croppings(pitch=tableNumber)
        self.crop_values = tools.find_extremes(calibration['outline'])

        # Parameters used to fix radial distortion
        radial_data = tools.get_radial_data()
        self.nc_matrix = radial_data['new_camera_matrix']
        self.c_matrix = radial_data['camera_matrix']
        self.dist = radial_data['dist']

    def start(self):
        super(Camera,self).run()

        while(cv2.waitKey(1) != 27): #while NOT pressing esc (27) key
            # Capture frame-by-frame
            self.set_frame()

            print "[Camera Thread] seting new frame . . . "

            # Display the resulting frame
            #cv2.imshow(name, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        self.end()

    def end(self):
        capture.release()
        self.exit()

    def set_frame(self):
        (status, frame) = self.capture.read()
        frame = self.fix_radial_distortion(frame)
        if status:
            self.frame = frame[
                self.crop_values[2]:self.crop_values[3],
                self.crop_values[0]:self.crop_values[1]
            ]

    def get_frame(self):
        return self.frame

    def fix_radial_distortion(self, frame):
        return cv2.undistort(
            frame, self.c_matrix, self.dist, None, self.nc_matrix)


class GUI(Thread):
    name = None     # name of GUI window
    camera = None   # camera from which the frames are received

    def __init__(self, name, camera):
        super(Camera,self).__init__()
        self.name = name
        self.camera = camera

    def start(self):
        super(GUI,self).run()
        while(cv2.waitKey(1) != 27): #while NOT pressing esc (27) key
            # Capture frame-by-frame
            frame = self.camera.get_frame()

            print "[GUI Thread] drawing new frame . . . "

            # Display the resulting frame
            cv2.imshow(self.name, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        self.stop()

    def stop(self):
        cv2.destroyAllWindows()


# class GUI:

#     # GUI variables
#     name = "Lucky Strike 7"     # GUI window name
#     camera = None               # Camera object from which frames can be received
#     frame = None                # Frame received from camera
#     frame_with_blank = None     # Blank (blank = BLACK, not "white") frame mask (vector filled with 0's)
#     blank = None                # Blank vector transformed into matrix with given camera frame format

#     def __init__(self, camera):
#         self.camera = camera
#         # self.frame = camera.capture.read()
#         # self.blank = np.zeros_like(frame)[:200, :, :]
#         # self.frame_with_blank = np.vstack((frame, self.blank))

#         # Define popup window panel
#         # cv2.namedWindow(self.name)
#         self.start()


#     def start(self):
#         while(cv2.waitKey(1) != 27): #while NOT pressing esc (27) key
#             # Capture frame-by-frame
#             ret, frame = self.camera.capture.read()

#             # Display the resulting frame
#             cv2.imshow(self.name,self.frame)
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break
#         self.stop()

#     def stop(self):
#         cap.release()
#         cv2.destroyAllWindows()




# class Camera:

#     capture = None      # Capture socket to read frames from camera
#     calibration = None  # Cropping calibration setup to specify tableNumber
#     crop_values = None  # Specified to crop down to the tableNumber outline
#     radial_data = None  # Radial data (?) property
#     nc_matrix = None    # NEW-CAMERA radial data, stored as matrix
#     c_matrix = None     # (old) camera radial data, stored as matrix
#     dist = None         # radial distortion

#     def __init__(self, port=0, tableNumber=0):
#         self.capture = cv2.VideoCapture(port)
#         calibration = tools.get_croppings(tableNumber=tableNumber)
#         self.crop_values = tools.find_extremes(calibration['outline'])

#         # Parameters used to fix radial distortion
#         radial_data = tools.get_radial_data()
#         print radial_data
#         self.nc_matrix = radial_data['new_camera_matrix']
#         self.c_matrix = radial_data['camera_matrix']
#         self.dist = radial_data['dist']

#     def fix_radial_distortion(self, frame):
#         return cv2.undistort(
#             frame, self.c_matrix, self.dist, None, self.nc_matrix)

#     def get_adjusted_center(self, frame):
#         # return (320-self.crop_values[0], 240-self.crop_values[2])
#         return (320, 240)

#     def get_frame(self):
#         status = True
#         frame = self.capture.read()
#         frame = self.fix_radial_distortion(frame)
#         if status:
#             return frame
#             return frame[
#                 self.crop_values[2]:self.crop_values[3],
#                 self.crop_values[0]:self.crop_values[1]
#             ]





# TODO: add no-comms option for testing
if __name__ == '__main__':
    main = Main()
    main.run()