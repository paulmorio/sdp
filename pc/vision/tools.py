import numpy as np
import cv2
import json
import socket
import os
import cPickle

PATH = os.path.dirname(os.path.realpath(__file__))
BLACK = (0, 0, 0)

# HSV Colors
WHITE_LOWER = np.array([1, 0, 100])
WHITE_HIGHER = np.array([36, 255, 255])

BLUE_LOWER = np.array([95., 50., 50.])
BLUE_HIGHER = np.array([110., 255., 255.])

RED_LOWER = np.array([0, 240, 140])
RED_HIGHER = np.array([9, 255, 255])

YELLOW_LOWER = np.array([9, 50, 50])
YELLOW_HIGHER = np.array([11, 255, 255])

PITCHES = ['Pitch_0', 'Pitch_1']


def get_zones(width, height,
              filename=PATH+'/calibrations/croppings.json', pitch=0):
    calibration = get_croppings(filename, pitch)
    zones_poly = [calibration[key] for key in ['Zone_0', 'Zone_1',
                                               'Zone_2', 'Zone_3']]

    maxes = [max(zone, key=lambda x: x[0])[0] for zone in zones_poly[:3]]
    mins = [min(zone, key=lambda x: x[0])[0] for zone in zones_poly[1:]]
    mids = [(maxes[i] + mins[i]) / 2 for i in range(3)]
    mids.append(0)
    mids.append(width)
    mids.sort()
    return [(mids[i], mids[i+1], 0, height) for i in range(4)]


def get_croppings(filename=PATH+'/calibrations/croppings.json', pitch=0):
    croppings = get_json(filename)
    return croppings[PITCHES[pitch]]


def get_json(filename=PATH+'/calibrations/calibrations.json'):
    _file = open(filename, 'r')
    content = json.loads(_file.read())
    _file.close()
    return content


def get_radial_data(pitch=0, filename=PATH+'/calibrations/undistort.txt'):
    _file = open(filename, 'r')
    data = cPickle.load(_file)
    _file.close()
    return data[pitch]


def get_colors(pitch=0, filename=PATH+'/calibrations/calibrations.json'):
    """
    Get colours from the JSON calibration file.
    Converts all
    """
    json_content = get_json(filename)
    machine_name = socket.gethostname().split('.')[0]
    pitch_name = 'PITCH0' if pitch == 0 else 'PITCH1'

    if machine_name in json_content:
        current = json_content[machine_name][pitch_name]
    else:
        current = json_content['default'][pitch_name]

    # convert mins and maxes into np.array
    for key in current:
        key_dict = current[key]
        if 'hsv_min' in key_dict:
            key_dict['hsv_min'] = np.array(tuple(key_dict['hsv_min']))
        if 'hsv_max' in key_dict:
            key_dict['hsv_max'] = np.array(tuple(key_dict['hsv_max']))
        if 'rgb_min' in key_dict:
            key_dict['rgb_min'] = np.array(tuple(key_dict['rgb_min']))
        if 'rgb_max' in key_dict:
            key_dict['rgb_max'] = np.array(tuple(key_dict['rgb_max']))

    return current


def save_colors(pitch, colors, filename=PATH+'/calibrations/calibrations.json'):
    json_content = get_json(filename)
    machine_name = socket.gethostname().split('.')[0]
    pitch_name = 'PITCH0' if pitch == 0 else 'PITCH1'

    # convert np.arrays into lists
    for key in colors:
        key_dict = colors[key]
        if 'hsv_min' in key_dict:
            key_dict['hsv_min'] = list(key_dict['hsv_min'])
        if 'hsv_max' in key_dict:
            key_dict['hsv_max'] = list(key_dict['hsv_max'])
        if 'rgb_min' in key_dict:
            key_dict['rgb_min'] = list(key_dict['rgb_min'])
        if 'rgb_max' in key_dict:
            key_dict['rgb_max'] = list(key_dict['rgb_max'])

    if machine_name in json_content:
        json_content[machine_name][pitch_name].update(colors)
    else:
        json_content[machine_name] = json_content['default']
        json_content[machine_name][pitch_name].update(colors)

    write_json(filename, json_content)


def save_croppings(pitch, data, filename=PATH+'/calibrations/croppings.json'):
    """
    Open the current croppings file and only change the croppings
    for the relevant pitch.
    """
    croppings = get_json(filename)
    croppings[PITCHES[pitch]] = data
    write_json(filename, croppings)


def write_json(filename=PATH+'/calibrations/calibrations.json', data={}):
    _file = open(filename, 'w')
    _file.write(json.dumps(data))
    _file.close()


def mask_pitch(frame, points):
    mask = frame.copy()
    points = np.array(points, np.int32)
    cv2.fillConvexPoly(mask, points, BLACK)
    hsv_mask = cv2.cvtColor(mask, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_mask, (0, 0, 0), (0, 0, 0))
    return cv2.bitwise_and(frame, frame, mask=mask)


def find_extremes(coords):
    left = min(coords, key=lambda x: x[0])[0]
    right = max(coords, key=lambda x: x[0])[0]
    top = min(coords, key=lambda x: x[1])[1]
    bottom = max(coords, key=lambda x: x[1])[1]
    return left, right, top, bottom


def find_crop_coordinates(frame, keypoints=None, width=520, height=285):
    """
    Get crop coordinated for the actual image based on masked version.

    Params:
        [int] width     fixed width of the image to crop to
        [int[ height    fixed height of the image to crop to

    Returns:
        A 4-tuple with crop values
    """
    frame_height, frame_width, channels = frame.shape
    if frame_width < width or frame_height < height:
        print 'get_crop_coordinates:', \
            'Requested size of the frame is smaller than the original frame'
        return frame
    else:
        x_min = min(keypoints, key=lambda x: x[0])[0]
        y_min = min(keypoints, key=lambda x: x[1])[1]
        x_max = max(keypoints, key=lambda x: x[0])[0]
        y_max = max(keypoints, key=lambda x: x[1])[1]

        return x_min, x_max, y_min, y_max


def crop(frame, size=None):
    """
    Crop a frame given the size.
    If size not provided, attempt to extract the field and crop.

    Params:
        [OpenCV Frame] frame    frame to crop
        [(x1,x2,y1,y2)] size
    """
    x_min, x_max, y_min, y_max = size
    return frame[y_min:y_max, x_min:x_max]
