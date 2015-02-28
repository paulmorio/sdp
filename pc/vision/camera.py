import cv2
import tools


class Camera(object):
    """
    Camera wrapper with frame pre-processing options.
    """
    def __init__(self, pitch, video_src=0, options=None):
        self.capture = cv2.VideoCapture(video_src)
        calibration = tools.get_croppings(pitch=pitch)
        self.crop_values = tools.find_extremes(calibration['outline'])

        # Set defaults
        self.options = {
            'crop': True,                   # Crop frame to isolate pitch
            'fix_radial_distortion': True,  # Fix radial lens distortion
        }

        # Apply custom options from arguments
        if options is not None:
            for key in options:
                if key in self.options:
                    self.options[key] = options[key]

        # Radial distortion parameters
        radial_data = tools.get_radial_data()
        self.nc_matrix = radial_data['new_camera_matrix']
        self.c_matrix = radial_data['camera_matrix']
        self.dist = radial_data['dist']

        # Cache previous frame in case of feed disruption
        self.current_frame = None

    def get_frame(self):
        """
        Retrieve a frame from the feed and pre-process according to options.
        :return: Cropped and undistorted frame.
        """
        status, frame = self.capture.read()
        if status:  # If a frame is received, process and return it
            if self.options['fix_radial_distortion']:  # Fix radial distortion
                frame = self.fix_radial_distortion(frame)
            if self.options['crop']:  # Crop the frame
                return frame[
                    self.crop_values[2]:self.crop_values[3],
                    self.crop_values[0]:self.crop_values[1]
                ]
            self.current_frame = frame
            return frame
        else:  # Return previous frame if the video feed dies
            print "Feed disrupted - no longer receiving new frames!"
            if self.current_frame is not None:
                return self.current_frame

    def fix_radial_distortion(self, frame):
        return cv2.undistort(
            frame, self.c_matrix, self.dist, None, self.nc_matrix)

    def get_adjusted_center(self):
        return 320 - self.crop_values[0], 240 - self.crop_values[2]

    def release(self):
        self.capture.release()


# Capture image and save to file if run from main (pitch 0 only)
if __name__ == '__main__':
    cam = Camera(0)
    frame = cam.get_frame()
    cv2.imwrite('test.png', frame)