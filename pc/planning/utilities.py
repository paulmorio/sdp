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

## Catcher state constants
OPENED = "open"
CLOSED = "closed"



