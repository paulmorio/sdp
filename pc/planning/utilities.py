# Planner and strategy state constants

# Planner Constants
BALL_UNREACHABLE = 'ball_unreachable'
BALL_OUR_ZONE = 'ball_our_zone'
POSSESSION = 'possession'
NOT_FACING_BALL = 'NOT_FACING_BALL'

# Strategy State Constants
INIT = 'init'
IDLE = 'idle'
GRABBER_CLOSED = 'grabber_closed'
GRABBER_OPEN = 'grabber_open'
FACING_BALL = 'facing_ball'
GRABBING_BALL = 'grabbing_ball'
FACING_DEFENDER = 'facing_defender'
FACING_GOAL = 'facing_goal'
BALL_IN_GRABBER_AREA = 'ball_in_grabber_area'
TESTING_GRAB = 'grab_test'
KICK = 'kick'
KICKED = 'kicked'
FIND_PATH = 'find_path'
HAS_LOS = 'has_los'
# Margin constants
ROTATE_MARGIN = 0.30  # in radians
DISPLACEMENT_MARGIN = 20  # in centimetres
GRAB_AREA_MARGIN = 10  # in centimetres
MARGIN_WIDTH_CM = 38.4
MARGIN_WIDTH_PX = 91.0
CM_PX_RATIO = MARGIN_WIDTH_CM / MARGIN_WIDTH_PX



def px_to_cm(px):
    """
    :param px: Pixels
    :return: Centimetre representation of the given pixels
    """
    return px * CM_PX_RATIO
