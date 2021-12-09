# module that holds the general game variables (Score, total dropped balls etc) as local variables.
# and the bigger objects (Playfield, Depot etc) also


import depot, crane, playfield, scoreArea, ongoing, balls
from constants import depotsize, craneareasize, playfieldsize, scoredisplayarea_size

depot = depot.Depot(depotsize)
crane = crane.Crane(craneareasize)
playfield = playfield.Playfield(playfieldsize)
score_area = scoreArea.ScoreArea(scoredisplayarea_size)

level = 4
balls_dropped = 0
score = 0
global_scorefactor = 1.0

def reset():
    """Initializes the game state"""
    #global score_area
    global level, balls_dropped, score, global_scorefactor

    depot.reset()
    crane.reset()
    ongoing.reset()
    playfield.reset()

    level = 4
    balls_dropped = 0
    score = 0
    global_scorefactor = 1.0

def drop_ball():
    """drops current ball from the Crane, puts next ball into Crane, generates new ball in the depot.
    And performs the connected bookkeeping (count dropped balls, levelup if needed)"""
    global balls_dropped, level
    crane.drop_ball()
    
    balls_dropped += 1
    if balls_dropped % 50 == 0:
        level += 1
        score_area.update_level()
    score_area.changed()

def tick():
    """performs update of the game state, called periodically as time passes."""
    playfield.tick()
    ongoing.tick()
    
def getscore():
    return score

def getlevel():
    return level

class GameStateError():
    pass