# Top-level planner state constants
NO_BALL = 'no_ball'  # Ball not yet seen, not in play areas (init state)
BALL_UNREACHABLE = 'ball_unreachable'  # Ball not in our margin
BALL_REACHABLE = 'ball_reachable'  # Ball in our margin
POSSESSION = 'have_possession'  # Our robot has the ball in its grabber

# Strategy state constants
DUMMY = 'dummy'
## Idle
REPOSITION = 'reposition'
REORIENT = 'reorient'
IDLE = 'idle'
