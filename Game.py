# class that holds the general game variables (Score, total dropped balls etc) as local variables.
# and the bigger objects (Playfield, Depot etc) also


import depot, crane, playfield, scoreArea, ongoing, balls
from constants import depotsize, craneareasize, playfieldsize, scoredisplayarea_size

def init():
    """Initializes the game state, including depot/crane/playfield constructor calls
    """
    global depot, crane, playfield, score_area
    global level, balls_dropped, score
    depot = depot.Depot(depotsize)
    crane = crane.Crane(craneareasize)
    playfield = playfield.Playfield(playfieldsize)
    score_area = scoreArea.ScoreArea(scoredisplayarea_size)
    level = 4
    balls_dropped = 0
    score = 0

# Level. Is the number of colors and the max weight of balls spawning in the depot, and factor for the score. 
# Starts at 4, increases every 50 Balls dropped.
#level = 4

# Total number of Balls dropped with the crane
#balls_dropped = 0

# Total score
#score = 0

def drop_ball():
    """drops current ball from the Crane, puts next ball into Crane, generates new ball in the depot.
    And performs the connected bookkeeping (count dropped balls, levelup if needed)"""
    global balls_dropped, level
    column = crane.getx()
    ongoing.drop_ball(crane.current_Ball, column+1)
    balls_dropped += 1
    if balls_dropped % 50 == 0:
        level += 1
        score_area.update_level()
    crane.current_Ball = depot.content[column][1]
    depot.content[column][1] = depot.content[column][0]
    depot.content[column][0] = balls.generate_ball()
    # force re-draws
    crane.changed = True
    depot.changed = True
    score_area.changed = True

def tick():
    """performs update of the game state, called periodically as time passes."""
    for event in ongoing.eventQueue:
        event.tick(playfield)

class GameStateError():
    pass