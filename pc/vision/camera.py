import cv2
import tools


class Camera(object):
    """
    Camera wrapper with frame pre-processing options.
    """
    def __init__(self, pitch=0, options=None):
        self.capture = cv2.VideoCapture(pitch)
        calibration = tools.get_croppings(pitch=pitch)
        self.crop_values = tools.find_extremes(calibration['outline'])

        # Set defaults
        self.options = {
            'crop': True,                   # Crop frame to isolate pitch
            'fix_radial_distortion': True,  # Fix radial lens distortion
            'normalize': False,             # Saturation normalization
            'background_sub': False         # Background subtraction feed
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

        # Background subtraction parameters
        self.background_sub = None

    def get_options(self):
        return self.options

    def set_options(self, options=None):
        """
        Set given options. If no options given then set all to defaults.
        """
        if not options:
            self.options = {
                'normalize': False,
                'background_sub': False
            }
        else:
            self.options = options

    def get_frame(self):
        """
        Retrieve a frame from the feed and pre-process according to options.
        :return: 2-dictionary with frame and, if chosen, the bg_sub
        """
        result = {}
        status, frame = self.capture.read()
        if status:  # If a frame is received, process and return it
            if self.options['crop']:  # Crop the frame
                frame = frame[
                    self.crop_values[2]:self.crop_values[3],
                    self.crop_values[0]:self.crop_values[1]
                ]
            if self.options['fix_radial_distortion']:  # Fix radial distortion
                frame = self.fix_radial_distortion(frame)
            if self.options['normalize']:
                frame = self.normalize(frame)
            if self.options['background_sub']:
                result['bg_sub'] = self.get_bg_sub(frame)
            result['frame'] = frame
            return result

    def fix_radial_distortion(self, frame):
        return cv2.undistort(
            frame, self.c_matrix, self.dist, None, self.nc_matrix
        )

    def normalize(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        frame[:, :, 1] = cv2.equalizeHist(frame[:, :, 1])
        return cv2.cvtColor(frame, cv2.COLOR_HSV2BGR)

    def get_bg_sub(self, frame):
        if self.background_sub is None:  # Generate bg sub on first run
            self.background_sub = cv2.BackgroundSubtractorMOG2(0, 30, False)
        return self.background_sub.apply(frame)

    def reset_bg_sub(self):
        self.background_sub = None

    def get_adjusted_center(self):
        return 320 - self.crop_values[0], 240 - self.crop_values[2]


class CameraGUI(object):
    WINDOW = "Lucky Number Seven - Camera Feed"
    RADIAL = "Fix RD"
    BG_SUB = "BG Subtract"
    NORMALIZE = "Normalize"

    def __init__(self, pitch=0):
        self.camera = Camera(pitch=pitch)

    def run(self):
        # Set up GUI
        cv2.namedWindow(self.WINDOW)

        # Set up option trackbars - reset bg sub on change
        init_pos = {key: 1 if val else 0 for (key, val) in
                    self.camera.options.iteritems()}
        cv2.createTrackbar(self.RADIAL, self.WINDOW,
                           init_pos['fix_radial_distortion'], 1,
                           lambda x: self.camera.reset_bg_sub())
        cv2.createTrackbar(self.BG_SUB, self.WINDOW,
                           init_pos['background_sub'], 1,
                           lambda x: self.camera.reset_bg_sub())
        cv2.createTrackbar(self.NORMALIZE, self.WINDOW,
                           init_pos['normalize'], 1,
                           lambda x: self.camera.reset_bg_sub())

        # Read and refresh
        while True:
            current_frame = self.camera.get_frame()

            # Show background subtraction window if option is selected
            if 'bg_sub' in current_frame:
                cv2.imshow(self.WINDOW, current_frame['bg_sub'])
            else:
                cv2.imshow(self.WINDOW, current_frame['frame'])

            self.update_camera_options()

            # Quit on 'q' keypress
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def update_camera_options(self):
        self.camera.options['fix_radial_distortion'] = \
            cv2.getTrackbarPos(self.RADIAL, self.WINDOW) == 1
        self.camera.options['background_sub'] = \
            cv2.getTrackbarPos(self.BG_SUB, self.WINDOW) == 1
        self.camera.options['normalize'] = \
            cv2.getTrackbarPos(self.NORMALIZE, self.WINDOW) == 1


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("pitch", help="Main pitch: 0, Second pitch: 1")
    args = parser.parse_args()

    gui = CameraGUI(pitch=int(args.pitch))
    gui.run()
