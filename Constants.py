# holds all constant values, like pixel counts, tick rates etc
# also performs calculations for positioning: 
# - Where is the depot/playfield/etc drawn.
# - Where in the depot area is the first/second/nth col drawn?

# (max) number of ticks to be calculated per second
max_FPS = 20

# speed of falling Balls, in tiles/sec
falling_speed = 2.0
# same in tiles/tick
falling_per_tick = falling_speed / max_FPS

# speed of tilting Seesaws, in 1/sec. For example 4.0 means 0.25sec to tilt to final position
tilting_speed = 4.0
# same in tilts/tick
tilting_per_tick = tilting_speed / max_FPS

# speed of Scoring. How fast does ball-removing travel (in Balls/sec)
scoring_speed = 5.0
# delay in ticks until next stage of scoring
scoring_delay = int(max_FPS / scoring_speed)


# width, height of the canvas
screensize = (1024, 768)

# this many px blank at the edge, to have a margin
global_xmargin = 10
global_ymargin = 10

# size of a Ball, in px
ballsize = (60, 40)

# horizontal space between cols in Playfield/Depot
colspacing = 5
# vertical space between two stacked Balls
rowspacing = 5

# Size of area for the depot, relative to screensize
depotsize_fraction = (0.7, 0.2)
depotsize = (screensize[0]*depotsize_fraction[0], screensize[1]*depotsize_fraction[1])
# Pixel coords of the top-left corner of the Depot. It is centered at the top for now.
depot_position_y = global_ymargin
depot_position_x = int(0.5*(1.0-depotsize_fraction[0])*screensize[0])
depot_position = (depot_position_x, depot_position_y)

# Calculate Pixel coords of the (top-left corner of the) first Ball in the depot, and 
# distance to second-to-left Ball in the depot.
# 8 cols of Balls use 8*ballsize[0] px plus 7*colspacing
px_used = 8*ballsize[0] + 7*colspacing
# Rest of the px is divided equally left and right
if px_used > depotsize[0]:
	raise ValueError("Depot not wide enough.")

depot_xleft = int(0.5*(depotsize[0] - px_used))
depot_x_perCol = ballsize[0]+colspacing
# => x-coord of Ball in col i is depot_left + i*depot_x_perCol

# same for y-direction. Two rows of Balls use (2*ballsize[1] + colspacing) px.
px_used = 2*ballsize[1] + colspacing
if px_used > depotsize[1]:
	raise ValueError("Depot not high enough.")

depot_ytop = int(0.5*(depotsize[1] - px_used))
depot_y_perRow = ballsize[1]+colspacing

# it should be sufficient to import these two pairs
depot_ballcoord = [depot_xleft, depot_ytop]
depot_ballspacing=[depot_x_perCol, depot_y_perRow]



# Size of area where the crane moves, relative to screensize
craneareasize_fraction = (0.7, 0.1)
craneareasize = (screensize[0]*craneareasize_fraction[0], screensize[1]*craneareasize_fraction[1])
# Pixel coords of the top-left corner of the crane area. For now, just 3 px below the depot
crane_position_x = depot_position_x
crane_position_y = depot_position_y + depotsize[1] + 3
cranearea_position = (crane_position_x, crane_position_y)

# Calculate pixel coords of the leftmost position where the Crane can be. And spacing to the second-to-left position etc
px_used = 8*ballsize[0] + 7*colspacing
if px_used > craneareasize[0]:
	raise ValueError("Crane Area not wide enough.")
cranearea_xleft = int(0.5*(craneareasize[0] - px_used))
cranearea_x_perCol = ballsize[0] + colspacing
# => x-coord of Crane in col i is cranearea_xleft + col*cranearea_x_perCol

if ballsize[1] > craneareasize[1]:
	raise ValueError("Crane Area not high enough.")
cranearea_ytop = int(0.5*(craneareasize[1] - ballsize[1]))

cranearea_ballcoord = [cranearea_xleft, cranearea_ytop]
cranearea_ballspacing=[0, cranearea_x_perCol]


# Size of area where the playfield is, including falling Balls, blocked tiles from the seesaws, weightdisplay
playfieldsize_fraction = (0.7, 0.6)
playfieldsize = (screensize[0]*playfieldsize_fraction[0], screensize[1]*playfieldsize_fraction[1])
# Pixel coords of the top-left corner of the playfield area. For now, just 3 px below the crane area
playfield_position_x = crane_position_x
playfield_position_y = crane_position_y + craneareasize[1] + 3
playfield_position = (playfield_position_x, playfield_position_y)

# bottom of playfield area has some space for displaying the current weight of that stack.
weightdisplayheight = 40

# Calculate px coords of the top-left Ball in the playfield
# x direction. The index in theplayfield.content[.][] counts from 1 instead of 0, to make the "dummy row" possible.
px_used = 8*ballsize[0] + 7*colspacing
if px_used > playfieldsize[0]:
	raise ValueError("Playfield not wide enough.")
playfield_ballcoord_x = int(0.5*(playfieldsize[0] - px_used))
playfield_ballcoord_perCol = ballsize[0]+colspacing
# => x-coord of Ball in playfield col i is playfield_ballcoord_x + (i-1)*playfield_ballcoord_perCol

# y direction. The index in theplayfield.content[][.] counts up from bottom instead of down.

px_used = 8*ballsize[1] + 7*rowspacing + weightdisplayheight
if px_used > playfieldsize[1]:
	raise ValueError("Playfield not high enough.")
playfield_ballcoord_y = int(0.5*(playfieldsize[1] - px_used))
playfield_ballcoord_perRow = ballsize[1] + colspacing
# => y-coord of Ball in playfield row j is playfield_ballcoord_y + (7-j)*playfield_ballcoord_perRow
playfield_ballcoord = [playfield_ballcoord_x, playfield_ballcoord_y]
playfield_ballspacing=[playfield_ballcoord_perCol, playfield_ballcoord_perRow]

# px position of weightdisplay
weightdisplay_y = playfield_ballcoord_y + 8*ballsize[1] + 7*rowspacing
weightdisplay_x = playfield_ballcoord_x + int(0.4*ballsize[0])
weightdisplay_x_perCol = ballsize[0]+colspacing
weightdisplay_coords = [weightdisplay_x, weightdisplay_y]
