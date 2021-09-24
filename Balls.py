# provides the Balls classes

# A Ball can either be Colored (has weight, 3 horizontal can Score, 5 vertical can Combine). Parent class is Ball.
# or Special (weight=0, has effect when landing or ongoing effect while in Playfield). 

# Balls have a draw() method. 
# Balls have a color attribute, for Scoring. color=-1 means colorless, never Scoring.
# The attribute isBall is True for ColoredBall and SpecialBall, and False for the placeholder-Dummys NotABall and Blocked. 
# Balls have a land() method. On placeholders it throws an error, ColoredBalls execute weight-check and scoring-check, 
# 	SpecialBalls trigger the effect of their specialty



import Colorschemes as colsce
ballcolors = colsce.simple_standard_ballcolors
textcols = colsce.simple_standard_textcolors

from pygame import Rect, font, Surface
import pygame
ballfont = font.SysFont("monospace", 24)

import random


# size of Balls in pixels. Is fix for now
from Constants import ballsize

from Ongoing import Scoring, SeesawTilting

class DummyBallError(Exception):
	pass

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
		raise DummyBallError("Dummy Blocked landed at ",coords,", this should never happen.")

class Colored_Ball(Ball):
	"""Child-class of Ball. Has a color (int, 1 <= color <= maxcolors) and a weight (int, 0 <= weight <= INT_MAX). Constructor is Colored_Ball(color, weight)."""
	# never change these globals, static for all ColoredBalls
	isBall = True
	def __init__(self, color, weight):
		self.color = color
		self.weight= weight
		
	def draw(self, surf, drawpos):
		"""draws this Ball onto pygame.Surface surf to offset-position drawpos. Returns None"""
		color = ballcolors[self.color]
		pixelpos_rect = Rect(drawpos, ballsize)
		ellipse = pygame.draw.ellipse(surf, color, pixelpos_rect, 0)
		weighttext = ballfont.render(str(self.weight), True, textcols[self.color])
		posx = drawpos[0]+0.2*ballsize[0]
		posy = drawpos[1]+0.2*ballsize[1]
		surf.blit(weighttext, (posx, posy))
	
	def land(self, coords, playfield, eventQueue):
		x,y = coords
		landingleft = (x%2==1) # landed on the left or the right side of a seesaw?
		# index of neighboring stack. x+1 if landed left, x-1 if landed right
		neighbor = x-1 + 2*landingleft
		
		### check if the seesaw will stay in position
		# indices in playfield.weights are 0..7, indices in playfield.content[.][] are 1..8. Shift by one.
		weightx = playfield.weights[x-1]
		weightneighbor = playfield.weights[neighbor-1]
		if weightneighbor < weightx: # dropping on the low side
			sesa_will_move = False 
		elif weightneighbor == weightx: # dropping on balanced
			if self.weight > 0:
				sesa_will_move = True
				new_state = 1 - 2*landingleft
		else: # dropping on high side
			sesa_will_move = (self.weight >= (weightneighbor - weightx))
			# new_state is -1 if the ball landed left. If sesa_will_move is False, this is never used and might as well be wrong. (@reviewer don't beat me pls)
			new_state = 1 - 2*landingleft
		
		### if yes, start moving
		if sesa_will_move:
			sesa_index = (x-1)//2
			old_state = playfield.seesaws[sesa_index]
			
			eventQueue.append(SeesawTilting(sesa_index, old_state, new_state))
			# Three cases are possible: a) new sesa position is balanced, b) sesa moves from balanced to tilted, 
			# c) from one-side-heavier to other-side-heavier. b and c throw the top Ball if it exists
			if new_state==0 or old_state==0:
				# move landing stack down by one
				for height in range(0, y):
					playfield.content[x][height] = playfield.content[x][height+1]
				playfield.content[x][y-1] = self
				# move neighboring stack up by one, insert a Blocked at the bottom
				for height in range(8, 0, -1):
					playfield.content[neighbor][height] = playfield.content[neighbor][height-1]
				playfield.content[neighbor][0] = Blocked()
				# TODO if old_state==0: obersten Ball werfen, falls er existiert
			else:
				# move landing stack down by two. Can safely assume two Blocked at the bottom
				for height in range(0, y-1):
					playfield.content[x][height] = playfield.content[x][height+2]
				playfield.content[x][y] = self
				# move neighboring stack up by two, insert two Blocked at the bottom
				for height in range(8, 2, -1):
					playfield.content[neighbor][height] = playfield.content[neighbor][height-2]
				playfield.content[neighbor][0] = Blocked()
				playfield.content[neighbor][1] = Blocked()
		### if not, check for Scoring or just place the Ball
		else:
			playfield.content[x][y] = self
			if playfield.check_Scoring(coords):
				print("Scored!")
				eventQueue.append(Scoring(coords, self))
			else:
				playfield.content[x][y] = self
				playfield.update_weights()
		
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