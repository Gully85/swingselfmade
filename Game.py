# class that holds the general game variables (Score, total dropped balls etc) as local variables.
# and the bigger objects (Playfield, Depot etc) also


import depot, crane, playfield, scoreArea
from constants import depotsize, craneareasize, playfieldsize, scoredisplayarea_size

def init():
    """Initializes the game state, including depot/crane/playfield constructor calls
    """
    global depot, crane, playfield, score_area
    depot = depot.Depot(depotsize)
    crane = crane.Crane(craneareasize)
    playfield = playfield.Playfield(playfieldsize)
    score_area = scoreArea.ScoreArea(scoredisplayarea_size)

# Level. Is the number of colors and the max weight of Ball spawning in the depot, and factor for the score. 
# Starts at 4, increases every 50 Balls dropped.
level = 4

# Total number of Balls dropped with the crane
balls_dropped = 0

# Total score
score = 0


class GameStateError():
    pass