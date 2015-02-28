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

# Threshold constants
ANGLE_THRESH = 0.2  # in radians
