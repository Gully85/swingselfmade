# holds all constant values, like pixel counts, tick rates etc
# also performs calculations for positioning:
# - Where is the depot/playfield/etc drawn.
# - Where in the depot area is the first/second/nth column drawn?

from typing import Tuple


# (max) number of ticks to be calculated per second
max_FPS: int = 50

startlevel: int = 4

endlevel: int = 10
endlevel_score_multiplier: float = 3.0

balls_per_level: int = 50

min_balls_between_Specials: int = 6

# number of columns in the play area. This must be an even number
num_columns: int = 8

# max allowed height before the game is lost
max_height: int = 8

# speed of falling Balls, in tiles/sec
falling_speed: float = 3.0
# same in tiles/tick
falling_per_tick: float = falling_speed / max_FPS

# Stop if falling Speed is higher than one tile per tick. This could break the FallingBall mechanic
if falling_per_tick > 1.0:
    raise ValueError("Falling Speed too high. Do not fall more than one tile per tick.")

# speed of tilting Seesaws, in 1/sec. For example 4.0 means 0.25sec to tilt to final position
tilting_speed: float = 2.0
# same in tilts/tick
tilting_per_tick: float = tilting_speed / max_FPS
# same in number of ticks to finish one full tilt
tilting_maxticks: int = int(2.0 / tilting_per_tick) + 1


# total time it takes for a thrown Ball to travel, in seconds
# (in case of [multiple times?] sideway fly-out, this is for each round)
thrown_ball_totaltime: float = 2.0
# trajectory parameter t goes from -1 to +1, increase this much in each tick
thrown_ball_dt: float = 2.0 / (max_FPS * thrown_ball_totaltime)
# thrown ball trajectory: y-value of highest point
thrown_ball_maxheight: float = 9.8
# if ball is thrown off the field, this position is their destination
thrown_ball_flyover_height: float = 7.0
# if ball is targeting a column, this is the height where they convert to a FallingBall.
# Trajectory looks strange if this is smaller than thrown_ball_maxheight :-)
thrown_ball_dropheight: float = 9.5

# speed of Scoring. How fast does ball-removing travel (in Balls/sec)
scoring_speed: float = 5.0
# delay in ticks until next stage of scoring
scoring_delay: float = int(max_FPS / scoring_speed)

# speed of Combining. How long does it take to Combine a vertical Five, in seconds
combining_totaltime: float = 1.0
# parameter t goes from 0.0 to 1.0, how much to add per tick
combining_dt: float = 1.0 / (max_FPS * combining_totaltime)

# time an Explosion is shown, in seconds
explosion_totaltime: float = 1.5
explosion_numticks: int = int(explosion_totaltime * max_FPS)


window_width: int = 1024
window_height: int = 768
window_size: Tuple[int, int] = (window_width, window_height)


# size of the canvas
# window_width, window_height = (1024, 768)
# window_size: Tuple[int, int] = (window_width, window_height)

# this many px blank at the edge, to have a margin
global_xmargin: int = 10
global_ymargin: int = 10


# horizontal space between columns in Playfield/Depot
column_spacing: int = 5
# vertical space between two stacked Balls
rowspacing: int = 5


finalscore_y: int = 50
