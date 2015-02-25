# Top-level planner state constants
NO_BALL = 'no_ball'  # Ball not yet seen, not in play areas (init state)
BALL_THEIR_A_ZONE = 'ball_their_attacker_zone'  # Ball in their attacker zone
BALL_THEIR_D_ZONE = 'ball_their_defender_zone'  # Ball in their defender zone
BALL_OUR_D_ZONE = 'ball_our_defender_zone'  # Ball in our defender zone
BALL_OUR_A_ZONE = 'ball_our_attacker_zone'  # Ball in our attacker zone
POSSESSION = 'have_possession'  # Our robot has the ball in its grabber

# Strategy state constants
DUMMY = 'dummy'
REPOSITION = 'reposition'
REORIENT = 'reorient'
IDLE = 'idle'
NONE = "no_state"
REORIENT_FREESPOT = "reorient_freespot"
REORIENT_DEFENDER = "reorient_defender"
REORIENT_PASSER = "reorient_passer"
OPEN_GRABBER = 'open_grabber'
CLOSE_GRABBER = 'close_grabber'
ROTATE = 'rotate'
PASS = 'pass'
SHOOT = 'shoot'
FACE_GOAL = 'face_goal'

WAIT_O_GRAB = 'wait_for_grabber_open'
WAIT_C_GRAB = 'wait_for_grabber_closed'
WAIT_REORIENT = 'wait_for_reorient'
WAIT_REORIENT_DEFENDER = 'wait_for_reorient_defender'
WAIT_REPOSITION = 'wait_for_reposition'
WAIT_FACE_GOAL = 'wait_for_face_goal'

# Catcher state constants
OPENED = "open"
CLOSED = "closed"

# Margin constants
ROTATE_MARGIN = 0.17  # in radians
DISPLACEMENT_MARGIN = 5  # in centimetres

GRAB_AREA_MARGIN = 10  # in centimetres