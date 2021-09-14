# provides the Balls classes

# A Ball can either be Colored (has weight, 3 horizontal can Score, 5 vertical can Combine). Parent class is Ball.
# or Special (weight=0, has effect when landing or ongoing effect while in Playfield). 

# Balls have a draw() method. 
# Balls have a color attribute, for Scoring. color=-1 means colorless, never Scoring.
# The attribute isBall is True for ColoredBall and SpecialBall, and False for the placeholder-Dummys NotABall and Blocked. 
# Balls have a land() method. On placeholders it throws an error, ColoredBalls execute weight-check and scoring-check, 
# 	SpecialBalls trigger the effect of their specialty



import Colorschemes as colsce
ballcols = colsce.simple_standard_ballcolors
textcols = colsce.simple_standard_textcolors

from pygame import Rect, font, Surface
import pygame
ballfont = font.SysFont("monospace", 24)

import random


# size of Balls in pixels. Is fix for now
from Constants import ballsize

from Ongoing import Scoring

class Ball:
	"""Parent class for Colored and Special Balls. Abstract class, should not be instanciated."""
	pass

class NotABall(Ball):
	"""Dummy class for places where there is no Ball. Empty Constructor."""
	# never change these globals, static vars for all NotABalls
	weight=0
	color =-1
	isBall = False
	def __init__(self):
		pass
	
	def draw(self, surf, drawpos):
		pass
	
	def land(self, coords, playfield, eventQueue):
		raise DummyBallError("Dummy NotABall landed at ",coords,", this should never happen.")

class Blocked(Ball):
	"""Dummy class for positions blocked by the seesaw state"""
	# never change these globals, static var for all Blockeds
	weight=0
	color=-1
	isBall = False
	def __init__(self):
		pass
	
	def draw(self, surf, drawpos): 
		"""just a black rectangle for now"""
		pygame.draw.rect(surf, (0,0,0), pygame.Rect(drawpos, ballsize))
		
	def land(self, coords, playfield, eventQueue):
		raise DummyBallError("Dummy Blocked landed at ",coord,", this should never happen.")

class Colored_Ball(Ball):
	"""Child-class of Ball. Has a color (int, 1 <= color <= maxcolors) and a weight (int, 0 <= weight <= INT_MAX). Constructor is Colored_Ball(color, weight)."""
	# never change these globals, static for all ColoredBalls
	isBall = True
	def __init__(self, color, weight):
		self.color = color
		self.weight= weight
		
	def draw(self, surf, drawpos):
		"""draws this Ball onto pygame.Surface surf to offset-position drawpos. Returns None"""
		col = ballcols[self.color]
		pixelpos_rect = Rect(drawpos, ballsize)
		ellipse = pygame.draw.ellipse(surf, col, pixelpos_rect, 0)
		weighttext = ballfont.render(str(self.weight), True, textcols[self.color])
		posx = drawpos[0]+0.2*ballsize[0]
		posy = drawpos[1]+0.2*ballsize[1]
		surf.blit(weighttext, (posx, posy))
	
	def land(self, coords, playfield, eventQueue):
		x,y = coords
		### check if the seesaw will stay in position
		# index of neighboring stack. x+1 if x is even (check x%2==0), x-1 if x is odd
		neighbor = x+1 - 2*(x%2==0)
		# indices in playfield.weights are 0..7, indices in playfield.content[.][] are 1..8. Shift by one.
		weightx = playfield.weights[x-1]
		weightneighbor = playfield.weights[neighbor-1]
		if weightneighbor < weightx:
			sesa_will_move = False #dropping on the already heavier side
		elif weightneighbor == weightx:
			sesa_will_move = (self.weight > 0)
		else:
			sesa_will_move = (self.weight >= (weightneighbor - weightx))
		
		sesa_will_move = False # test
		### if yes, start moving
		if sesa_will_move:
			#TODO
			pass
		else:
			playfield.content[x][y] = self
			if playfield.check_Scoring(coords):
				print("Scored!")
				eventQueue.append(Scoring(coords, self))
			else:
				playfield.content[x][y] = self
		
		#eventQueue.remove(self)
		


class Special_Ball(Ball):
	"""Child-class of Ball. Has weight=0 and type (int, 0 < type <= 1, this will grow as more types are added).
	Types are (for now):
	0: Joker. Counts as any color for the purpose of Scoring a horizontal.
	1: Bomb. Upon landing, destroy all neighboring Balls (3x3 area centered on the Bomb spot). 
	Constructor is Special_Ball(type)"""
	
	weight = 0 # shared static var by all Special_Balls. Never change this.
	isBall = True
	def __init__(self, type):
		self.type = type
	
	def draw(self, surf, drawpos):
		pass #TODO
		
def generate_starting_Ball():
	color = random.randint(1,4)
	weight= random.randint(1,4)
	the_ball = Colored_Ball(color, weight)
	#print("Generating random Ball. Color={}, Weight={}.".format(color,weight))
	return the_ball