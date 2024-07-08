# holds all constant values, like pixel counts, tick rates etc
# also performs calculations for positioning:
# - Where is the depot/playfield/etc drawn.
# - Where in the depot area is the first/second/nth column drawn?

from typing import Tuple, List


# (max) number of ticks to be calculated per second
max_FPS: int = 50

startlevel: int = 4

endlevel: int = 10
endlevel_score_multiplier: float = 3.0

balls_per_level: int = 50

min_balls_between_Specials: int = 6

# number of columns in the play area. This must be an even number
num_columns: int = 8

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

# size of a Ball, in px
ball_size = (60, 40)

# horizontal space between columns in Playfield/Depot
column_spacing: int = 5
# vertical space between two stacked Balls
rowspacing: int = 5

# Size of area for the depot, relative to screensize
depot_width_fraction, depot_height_fraction = (0.7, 0.2)
depotsize: Tuple[int] = (
    int(window_width * depot_width_fraction),
    int(window_height * depot_height_fraction),
)
# Pixel coordinates of the top-left corner of the Depot.
depot_position_y: int = global_ymargin
depot_position_x: int = int(0.2 * (1.0 - depot_width_fraction) * window_width)
depot_position: Tuple[int, int] = (depot_position_x, depot_position_y)

# Calculate Pixel coords of the (top-left corner of the) first Ball in the depot, and
# distance to second-to-left Ball in the depot.
# 8 cols of Balls use 8*ballsize[0] px plus 7*colspacing
px_used: int = 8 * ball_size[0] + 7 * column_spacing
# Rest of the px is divided equally left and right
if px_used > depotsize[0]:
    raise ValueError("Depot not wide enough.")

depot_xleft: int = int(0.5 * (depotsize[0] - px_used))
depot_x_perCol: int = ball_size[0] + column_spacing
# => x-coord of Ball in col i is depot_left + i*depot_x_perCol

# same for y-direction. Two rows of Balls use (2*ballsize[1] + colspacing) px.
px_used: int = 2 * ball_size[1] + column_spacing
if px_used > depotsize[1]:
    raise ValueError("Depot not high enough.")

depot_ytop: int = int(0.5 * (depotsize[1] - px_used))
depot_y_perRow: int = ball_size[1] + column_spacing

# it should be sufficient to import these two pairs
depot_ballcoord: List[int] = [depot_xleft, depot_ytop]
depot_ballspacing: List[int] = [depot_x_perCol, depot_y_perRow]

# Size of area where the crane moves, relative to screensize
craneareasize_fraction: Tuple[int, int] = (0.7, 0.1)
craneareasize: Tuple[int, int] = (
    int(window_width * craneareasize_fraction[0]),
    int(window_height * craneareasize_fraction[1]),
)
# Pixel coords of the top-left corner of the crane area. For now, just 3 px below the depot
crane_position_x: int = depot_position_x
crane_position_y: int = depot_position_y + depotsize[1] + 3
cranearea_position: Tuple[int, int] = (crane_position_x, crane_position_y)

# Calculate pixel coords of the leftmost position where the Crane can be. And spacing to the second-to-left position etc
px_used = 8 * ball_size[0] + 7 * column_spacing
if px_used > craneareasize[0]:
    raise ValueError("Crane Area not wide enough.")
cranearea_xleft: int = int(0.5 * (craneareasize[0] - px_used))
cranearea_x_perCol: int = ball_size[0] + column_spacing
# => x-coord of Crane in col i is cranearea_xleft + col*cranearea_x_perCol

if ball_size[1] > craneareasize[1]:
    raise ValueError("Crane Area not high enough.")
cranearea_ytop: int = int(0.5 * (craneareasize[1] - ball_size[1]))

cranearea_ballcoord: List[int] = [cranearea_xleft, cranearea_ytop]
cranearea_ballspacing: List[int] = [0, cranearea_x_perCol]


# Size of area where the playfield is, including falling Balls, blocked tiles from the seesaws, weightdisplay
playfieldsize_fraction: Tuple[float, float] = (0.7, 0.6)
playfieldsize: Tuple[int, int] = (
    int(window_width * playfieldsize_fraction[0]),
    int(window_height * playfieldsize_fraction[1]),
)
# Pixel coords of the top-left corner of the playfield area. For now, just 3 px below the crane area
playfield_position_x: int = crane_position_x
playfield_position_y: int = crane_position_y + craneareasize[1] + 3
playfield_position: Tuple[int, int] = (playfield_position_x, playfield_position_y)

# bottom of playfield area has some space for displaying the current weight of that stack.
weightdisplayheight: int = 40

# Calculate px coords of the top-left Ball in the playfield
# x direction. The index in theplayfield.content[.][] counts from 1 instead of 0, to make the "dummy row" possible.
px_used = 8 * ball_size[0] + 7 * column_spacing
if px_used > playfieldsize[0]:
    raise ValueError("Playfield not wide enough.")
playfield_ballcoord_x: int = int(0.5 * (playfieldsize[0] - px_used))
playfield_ballcoord_perCol: int = ball_size[0] + column_spacing
# => x-coord of Ball in playfield col i is playfield_ballcoord_x + (i-1)*playfield_ballcoord_perCol

# y direction. The index in theplayfield.content[][.] counts up from bottom instead of down.
px_used = 8 * ball_size[1] + 7 * rowspacing + weightdisplayheight
if px_used > playfieldsize[1]:
    raise ValueError("Playfield not high enough.")
playfield_ballcoord_y: int = int(0.5 * (playfieldsize[1] - px_used))
playfield_ballcoord_perRow: int = ball_size[1] + column_spacing
# => y-coord of Ball in playfield row j is playfield_ballcoord_y + (7-j)*playfield_ballcoord_perRow
playfield_ballcoord: Tuple[int, int] = [playfield_ballcoord_x, playfield_ballcoord_y]
playfield_ballspacing: Tuple[int, int] = [
    playfield_ballcoord_perCol,
    playfield_ballcoord_perRow,
]


def pixel_coord_in_playfield(playfield_coords: Tuple[int]) -> List[int]:
    """Takes playfield-coordinate (x,y), usually 0..7 (but
    values outside are allowed), returns pixel coordinate of the
    top-left corner of that position in playfield."""
    playfield_x, playfield_y = playfield_coords
    px_x: int = playfield_ballcoord[0] + playfield_x * playfield_ballspacing[0]
    px_y: int = playfield_ballcoord[1] + (7.0 - playfield_y) * playfield_ballspacing[1]

    return [px_x, px_y]


# px position of weightdisplay
weightdisplay_y: int = playfield_ballcoord_y + 8 * ball_size[1] + 8 * rowspacing
weightdisplay_x: int = playfield_ballcoord_x + int(0.4 * ball_size[0])
weightdisplay_x_per_column: int = ball_size[0] + column_spacing
weightdisplay_coords: List[int] = [weightdisplay_x, weightdisplay_y]


# area where the score-display is. Located 5px to the right of the playfield-area
px_used = playfield_position_x + playfieldsize[0]

scoredisplayarea_position_x: int = px_used + 5
scoredisplayarea_position_y: int = playfield_position_y
scoredisplayarea_position: Tuple[int, int] = (
    scoredisplayarea_position_x,
    scoredisplayarea_position_y,
)

scoredisplayarea_size_x: int = window_width - px_used - global_xmargin
scoredisplayarea_size_y: int = playfieldsize[1]
scoredisplayarea_size: Tuple[int, int] = (
    scoredisplayarea_size_x,
    scoredisplayarea_size_y,
)

finalscore_y: int = 50
