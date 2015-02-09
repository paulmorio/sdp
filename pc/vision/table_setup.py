import cv2
import numpy as np
import tools
import argparse

FRAME_NAME = 'Table Setup'

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (255, 0, 0)
GREEN = (0, 255, 0)
RED = (0, 0, 255)

distort_data = tools.get_radial_data()
NCMATRIX = distort_data['new_camera_matrix']
CMATRIX = distort_data['camera_matrix']
DIST = distort_data['dist']


class TableSetup(object):
    """
    Set up crop outline and table margin outlines.
    """

    def __init__(self, pitch, vid_src=0):
        self.pitch = pitch
        self.color = RED
        self.camera = cv2.VideoCapture(vid_src)
        self.image = None

        # Discard first image as this is usually corrupt
        self.camera.read()

        keys = ['outline', 'Zone_0', 'Zone_1', 'Zone_2', 'Zone_3']
        self.data = self.drawing = {}

        # Create keys
        for key in keys:
            self.data[key] = []
            self.drawing[key] = []

    def run(self):
        cv2.namedWindow(FRAME_NAME)
        cv2.setMouseCallback(FRAME_NAME, self.draw)

        status, image = self.camera.read()

        self.image = cv2.undistort(image, CMATRIX, DIST, None, NCMATRIX)

        # Get user clicks for image boundaries
        self.get_pitch_outline()
        self.get_zone('Zone_0', 'draw LEFT Defender')
        self.get_zone('Zone_1', 'draw LEFT Attacker')
        self.get_zone('Zone_2', 'draw RIGHT Attacker')
        self.get_zone('Zone_3', 'draw RIGHT Defender')
        self.get_goal('Zone_0')
        self.get_goal('Zone_3')

        print 'Press any key to finish.'
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        self.camera.release()
        # Write out the data
        tools.save_croppings(pitch=self.pitch, data=self.data)

    def reshape(self):
        return np.array(self.data[self.drawing], np.int32).reshape((-1, 1, 2))

    def draw_poly(self, points):
        cv2.polylines(self.image, [points], True, self.color)
        cv2.imshow(FRAME_NAME, self.image)

    def get_zone(self, key, message):
        print '%s. %s' % (message, "Continue by pressing q")
        self.drawing, k = key, True

        while k != ord('q'):
            cv2.imshow(FRAME_NAME, self.image)
            k = cv2.waitKey(100) & 0xFF

        self.draw_poly(self.reshape())

    def get_pitch_outline(self):
        """
        Have the user define pitch areas.
        """
        self.get_zone('outline', 'Draw the outline of the pitch. '
                                 'Press q to continue...')

        # Set up black mask to remove overflows
        self.image = tools.mask_pitch(self.image, self.data[self.drawing])

        # Get crop size based on points
        size = tools.find_crop_coordinates(self.image, self.data[self.drawing])
        self.image = self.image[size[2]:size[3], size[0]:size[1]]

        cv2.imshow(FRAME_NAME, self.image)

    def draw(self, event, x, y, flags, param):
        """
            Callback for mouse events.
            Unused args flags, param are passed by the caller.
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            color = self.color
            cv2.circle(self.image, (x-1, y-1), 2, color, -1)
            self.data[self.drawing].append((x, y))

    def get_goal(self, zone):
        """
            Returns the top and bottom corner of the goal in zone.
        """
        coords = self.data[zone]
        reverse = int(zone[-1]) % 2
        goal_coords = sorted(coords, reverse=reverse)[:2]
        if goal_coords[0][1] > goal_coords[1][1]:
            top_corner = goal_coords[1]
            bottom_corner = goal_coords[0]
        else:
            top_corner = goal_coords[0]
            bottom_corner = goal_coords[1]
        self.data[zone + '_goal'] = [top_corner, bottom_corner]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('pitch', help='Select pitch to be cropped [0, 1]')
    args = parser.parse_args()
    pitch_num = int(args.pitch)
    assert pitch_num in [0, 1]
    c = TableSetup(pitch=pitch_num)
    c.run()