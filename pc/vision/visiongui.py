import cv2
from colours import BGR_COMMON
import numpy as np
import tools
import warnings


warnings.filterwarnings("ignore", category=FutureWarning)


TEAM_COLORS = set(['yellow', 'blue'])
VISION = 'Lucky Number Seven'


class VisionGUI(object):

    def __init__(self, pitch):
        self.pitch = pitch
        self.zones = None
        cv2.namedWindow(VISION)

    def to_info(self, args):
        """
        Convert a tuple into a vector
        Return a Vector
        """
        x, y, angle, velocity = None, None, None, None
        if args is not None:
            if 'location' in args:
                x = args['location'][0] \
                    if args['location'] is not None else None
                y = args['location'][1] \
                    if args['location'] is not None else None

            elif 'x' in args and 'y' in args:
                x = args['x']
                y = args['y']

            if 'angle' in args:
                angle = args['angle']

            if 'velocity' in args:
                velocity = args['velocity']

        return {'x': x, 'y': y, 'angle': angle, 'velocity': velocity}

    def draw(self, frame, model_positions,
             regular_positions, fps, our_color, our_side):
        """
        Draw information onto the GUI given positions from the vision and
        post processing.
        NOTE: model_positions contains coordinates with y coordinate reversed!
        """
        # Get general information about the frame
        frame_height, frame_width, channels = frame.shape

        # Draw dividers for the zones
        self.draw_zones(frame, frame_width, frame_height)

        their_color = list(TEAM_COLORS - set([our_color]))[0]

        key_color_pairs = zip(
            ['our_defender', 'their_defender',
             'our_attacker', 'their_attacker'],
            [our_color, their_color]*2)

        self.draw_ball(frame, regular_positions['ball'])

        for key, color in key_color_pairs:
            self.draw_robot(frame, regular_positions[key], color)

        # Draw fps on the canvas
        if fps is not None:
            self.draw_text(frame, 'FPS: %.1f' % fps,
                           0, 10, BGR_COMMON['green'], 1)

        # Extend image downwards and draw states.
        blank = np.zeros_like(frame)[:200, :, :]
        frame_with_blank = np.vstack((frame, blank))

        if model_positions and regular_positions:
            for key in ['ball', 'our_defender', 'our_attacker',
                        'their_defender', 'their_attacker']:
                if model_positions[key] and regular_positions[key]:
                    self.data_text(
                        frame_with_blank, (frame_width, frame_height), our_side,
                        key, model_positions[key].x, model_positions[key].y,
                        model_positions[key].angle,
                        model_positions[key].velocity)
                    self.draw_velocity(
                        frame_with_blank, (frame_width, frame_height),
                        model_positions[key].x, model_positions[key].y,
                        model_positions[key].angle,
                        model_positions[key].velocity)

        cv2.imshow(VISION, frame_with_blank)

    def draw_zones(self, frame, width, height):
        # Re-initialize zones in case they have not been initialized
        if self.zones is None:
            self.zones = tools.get_zones(width, height, pitch=self.pitch)

        for zone in self.zones:
            cv2.line(frame, (zone[1], 0), (zone[1], height),
                     BGR_COMMON['orange'], 1)

    def draw_ball(self, frame, position_dict):
        if position_dict and position_dict['x'] and position_dict['y']:
            frame_height, frame_width, _ = frame.shape
            self.draw_line(
                frame, ((int(position_dict['x']), 0),
                        (int(position_dict['x']), frame_height)), 1)
            self.draw_line(
                frame, ((0, int(position_dict['y'])),
                        (frame_width, int(position_dict['y']))), 1)

    def draw_dot(self, frame, location):
        if location is not None:
            cv2.circle(frame, location, 2, BGR_COMMON['white'], 1)

    def draw_robot(self, frame, position_dict, color):
        if position_dict['box']:
            cv2.polylines(frame, [np.array(position_dict['box'])],
                          True, BGR_COMMON[color], 2)

        if position_dict['front']:
            p1 = (position_dict['front'][0][0], position_dict['front'][0][1])
            p2 = (position_dict['front'][1][0], position_dict['front'][1][1])
            cv2.circle(frame, p1, 3, BGR_COMMON['white'], -1)
            cv2.circle(frame, p2, 3, BGR_COMMON['white'], -1)
            cv2.line(frame, p1, p2, BGR_COMMON['red'], 2)

        if position_dict['dot']:
            cv2.circle(
                frame, (int(position_dict['dot'][0]),
                        int(position_dict['dot'][1])),
                4, BGR_COMMON['black'], -1)

        if position_dict['direction']:
            cv2.line(
                frame, position_dict['direction'][0],
                position_dict['direction'][1],
                BGR_COMMON['orange'], 2)

    def draw_line(self, frame, points, thickness=2):
        if points is not None:
            cv2.line(frame, points[0], points[1], BGR_COMMON['red'], thickness)

    def data_text(self, frame, frame_offset, our_side,
                  text, x, y, angle, velocity):
        if x is not None and y is not None:
            frame_width, frame_height = frame_offset
            if text == "ball":
                y_offset = frame_height + 130
                draw_x = 30
            else:
                x_main = lambda zz: (frame_width/4)*zz
                x_offset = 30
                y_offset = frame_height+20

                if text == "our_defender":
                    draw_x = x_main(0) + x_offset
                elif text == "our_attacker":
                    draw_x = x_main(2) + x_offset
                elif text == "their_defender":
                    draw_x = x_main(3) + x_offset
                else:
                    draw_x = x_main(1) + x_offset

                if our_side == "right":
                    draw_x = frame_width-draw_x - 80

            self.draw_text(frame, text, draw_x, y_offset)
            self.draw_text(frame, 'x: %.2f' % x, draw_x, y_offset + 10)
            self.draw_text(frame, 'y: %.2f' % y, draw_x, y_offset + 20)

            if angle is not None:
                self.draw_text(frame, 'angle: %.2f' % angle,
                               draw_x, y_offset + 30)

            if velocity is not None:
                self.draw_text(frame, 'velocity: %.2f' % velocity,
                               draw_x, y_offset + 40)

    def draw_text(self, frame, text, x, y,
                  color=BGR_COMMON['green'], thickness=1.3, size=0.3):
        if x is not None and y is not None:
            cv2.putText(frame, text, (int(x), int(y)),
                        cv2.FONT_HERSHEY_SIMPLEX, size, color, thickness)

    def draw_velocity(self, frame, frame_offset, x, y, angle, vel, scale=10):
        if not (None in [frame, x, y, angle, vel]) and vel is not 0:
            frame_width, frame_height = frame_offset
            r = vel*scale
            y = frame_height - y
            start_point = (x, y)
            end_point = (x + r * np.cos(angle), y - r * np.sin(angle))
            self.draw_line(frame, (start_point, end_point))


# Dummy function for opencv trackbar response
def nothing(x):
    pass