# Planner and strategy state constants

# Planner Constants
BALL_UNREACHABLE = 'ball_unreachable'
BALL_OUR_ZONE = 'ball_our_zone'
POSSESSION = 'possession'

# Strategy State Constants
INIT = 'init'
IDLE = 'idle'
GRABBER_CLOSED = 'grabber_closed'
GRABBER_OPEN = 'grabber_open'
FACING_BALL = 'facing_ball'
FACING_DEFENDER = 'facing_defender'
BALL_IN_GRABBER_AREA = 'ball_in_grabber_area'
TESTING_GRAB = 'grab_test'
KICK = 'kick'

# Margin constants
ROTATE_MARGIN = 0.13  # in radians
DISPLACEMENT_MARGIN = 20  # in centimetres
GRAB_AREA_MARGIN = 10  # in centimetres
MARGIN_WIDTH_CM = 38.4
MARGIN_WIDTH_PX = 91.0
CM_PX_RATIO = MARGIN_WIDTH_CM / MARGIN_WIDTH_PX

# Threshold constants
ANGLE_THRESH = 0.2  # in radians


def px_to_cm(px):
    """
    :param px: Pixels
    :return: Centimetre representation of the given pixels
    """
    return px * CM_PX_RATIO
