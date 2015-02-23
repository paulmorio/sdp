# Top-level planner state constants
NO_BALL = 'no_ball'  # Ball not yet seen, not in play areas (init state)
BALL_THEIRATTACKER = 'ball_theirattacker'  # Ball in their attacker zone
BALL_THEIRDEFENDER = 'ball_theirdefender'  # Ball in their defender zone
BALL_OURDEFENDER = 'ball_ourdefender'  # Ball in our defender zone
BALL_OURATTACKER = 'ball_ourattacker'  # Ball in our attacker zone
POSSESSION = 'have_possession'  # Our robot has the ball in its grabber

# Strategy state constants
DUMMY = 'dummy'
## Idle
REPOSITION = 'reposition'
REORIENT = 'reorient'
IDLE = 'idle'
## NON-IDLE
REORIENT_FREESPOT = "reorient_freespot"
REORIENT_DEFENDER = "reorient_defender"
OPEN_GRABBER = 'open_grabber'
CLOSE_GRABBER = 'close_grabber'
ROTATE = 'rotate'

## CATCHER STATE
OPENED = "open"
CLOSED = "closed"

NONE = "no state!"