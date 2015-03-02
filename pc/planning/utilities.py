# Planner and strategy state constants

# Planner Constants
BALL_UNREACHABLE = 'ball_unreachable'
BALL_OUR_ZONE = 'ball_our_zone'
POSSESSION = 'possession'
TURNING_TO_BALL = 'turning_to_ball'

# Strategy State Constants
INIT = 'init'
IDLE = 'idle'
GRABBER_CLOSED = 'grabber_closed'
KICKING = 'grabber_open'
OPENING_GRABBER = 'opening_grabber'
GRABBING_BALL = 'grabbing_ball'
FACING_GOAL = 'facing_goal'
BALL_IN_GRABBER_AREA = 'ball_in_grabber_area'
KICK = 'kick'
KICKED = 'kicked'
FINDING_PATH = 'finding_path'
TURNING_TO_DEFENDER = 'turning_to_def'

# Margin constants
ROTATE_MARGIN = 0.30  # in radians
DISPLACEMENT_MARGIN = 20  # in centimetres
GRAB_AREA_MARGIN = 10  # in centimetres
DANGER_ZONE_CM = 20