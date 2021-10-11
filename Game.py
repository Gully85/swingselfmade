# class that holds the general game variables (Score, total dropped balls etc) as local variables.
# and the bigger objects (Playfield, Depot etc) also

import Depot, Crane, Playfield
from Constants import depotsize, craneareasize, playfieldsize

def init():
	"""Initializes the game state, including depot/crane/playfield constructor calls
	"""
	global depot, crane, playfield
	depot = Depot.Depot(depotsize)
	crane = Crane.Crane(craneareasize)
	playfield = Playfield.Playfield(playfieldsize)

class SwingGame:
	"""Holds Variables and Objects for the game-state.
	depot: Depot as defined in Depot.py
	crane: Crane as defined in Crane.py
	playfield: Playfield as defined in Playfield.py
	(the eventQueue is still a local variable in Ongoing.py)
	score: int
	balls_dropped: int
	level: int
	"""
	
	