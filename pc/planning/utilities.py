# Planner Constants
BALL_NOT_VISIBLE = 'ball_unreachable'
BALL_OUR_ZONE = 'ball_our_zone'
POSSESSION = 'possession'
BALL_NOT_IN_OUR_ZONE = 'ball_not_in_our_zone'
FINDING_BALL = 'finding_ball'

# Strategy State Constants
INIT = 'init'
IDLE = 'idle'
GRABBER_CLOSED = 'grabber_closed'
MOVING_TO_BALL = 'moving_to_ball'
OPENING_GRABBER = 'opening_grabber'
GRABBING_BALL = 'grabbing_ball'
FACING_GOAL = 'facing_goal'
BALL_IN_GRABBER_AREA = 'ball_in_grabber_area'
KICK = 'kick'
KICKED = 'kicked'
FINDING_PATH = 'finding_path'
TURNING_TO_DEFENDER = 'turning_to_def'
TURNING_TO_BALL = 'turning_to_ball'
TURNING_TO_GOAL = 'turning_to_goal'
FACING_BALL = 'facing_ball'

# Margin constants
ROTATE_MARGIN = 0.17  # in radians
DISPLACEMENT_MARGIN = 20  # in centimetres
GRAB_AREA_MARGIN = 10  # in centimetres
DANGER_ZONE_CM = 20