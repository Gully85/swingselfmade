# provides the Playfield class. The playfield has 8 stacks of Balls 
# (lowest 0-2 are blocked, depending on seesaw state). An empty space in the playfield 
# is represented as None, same for a blocked space at the bottom.
# content[0][] and content[

debugprints = False

from pygame import Rect, Surface, font
from Balls import *
from Constants import playfield_ballcoord, playfield_ballspacing, weightdisplay_coords, weightdisplay_x_perCol

#weightdisplayheight = 40
weightdisplayfont = font.SysFont("Arial", 12)

class Playfield:
	"""Information about the current Playfield. Variables:
		content (10x8 array of either NotABall or Blocked or Balls). Leftmost and Rightmost 
			cols are all Blocked, as a dummy, to simplify boundaries. Second index counts y from 
			bottom (index=0) to highest position (index=7).
		weights (8 ints, left to right). Keep in mind that content has a dummy row: weights[0] is 
			the total weight of all Balls in content[1][.]
		seesaw (4 ints, left to right). 0 indicates equal 
			weights, -1 for heavier left, +1 for heavier right).
		size (2 ints). Size of drawing are in px
		surf (pygame.Surface)
	Constructor takes size in pixels."""
	
	def __init__(self, size):
		self.content = [[ Blocked(),Blocked(),Blocked(),Blocked(), Blocked(),Blocked(),Blocked(),Blocked() ]]
		for i in range(8):
			self.content.append([ Blocked(),NotABall(),NotABall(),NotABall(), NotABall(),NotABall(),NotABall(),NotABall() ])
		self.content.append([ Blocked(),Blocked(),Blocked(),Blocked(), Blocked(),Blocked(),Blocked(),Blocked() ])
		
		self.weights = [0,0,0,0, 0,0,0,0]
		self.seesaws = [0,  0,   0,  0]
		self.size = size
		self.surf = Surface(size)
		self.changed = True # if anything changed since the last tick
		
	def update_weights(self):
		"""calculate all weights"""
		for x in range(1,9):
			sum=0
			for y in range(8):
				sum += self.content[x][y].weight
			self.weights[x-1]=sum
		
	def update_seesaws(self):
		"""compares seesaw state with weights, update seesaws if necessary. Returns list of 4 Bools, True where state changed."""
		ret = [False, False, False, False]
		for sesa in range(4):
			left = 1 + sesa*2
			right= 2 + sesa*2
			
			if self.weights[left] > self.weights[right]:
				newstate = -1
			elif self.weights[left] == self.weights[right]:
				newstate = 0
			else:
				newstate = 1
			
			if newstate != self.seesaw[sesa]:
				ret[sesa] = True
				self.seesaw[sesa] = newstate
		return ret
		
	def check_Scoring(self, coords):
		"""True if the Ball at the given coords should start a Scoring. It must be part of a horizontal 3-line for that."""
		x,y = coords
		content = self.content
		ball = content[x][y]
		color = ball.color
		# The ball itself has the correct color. Three possible cases: 
		# 1-Left and 2-Left have the correct color
		# 1-Left and 1-Right 
		# 1-Right and 2-Right
		# Difficulty: Can't access self.content[x-2] or [x+2] blindly, that would sometimes be out of array bounds.
		
		# catch the edge cases (coords are at the far-left or far-right) separately. If no edge case, [x-2] and [x+2]
		# can be accessed safely (might be Ball.Blocked objects with color=-1)
		
		#print("Entering scoring check at ",coords)
		if x == 1:
			#print("left edge, scored")
			return content[2][y].color == color and content[3][y].color == color
		elif x == 8:
			#print("right edge, scored")
			return content[7][y].color == color and content[6][y].color == color
		else:
			#print("colors of the 5 balls to check: ", content[x-2][y].color, content[x-1][y].color, content[x][y].color, content[x+1][y].color, content[x+2][y].color)
			return (( content[x-2][y].color == color and content[x-1][y].color == color ) or
				   (  content[x-1][y].color == color and content[x+1][y].color == color ) or
				   (  content[x+1][y].color == color and content[x+2][y].color == color ))


	def draw(self):
		"""draws the Playfield including all Balls. Returns surface."""
		self.surf.fill((127,127,127))
		
		# draw all the Balls (and Blocked Positions), iterate over self.content
		for x in range(1,9):
			xcoord = playfield_ballcoord[0] + (x-1)*(playfield_ballspacing[0])
			for y in range(8):
				ycoord = playfield_ballcoord[1] + (7-y)*(playfield_ballspacing[1])
				if debugprints:
					if isinstance(self.content[x][y], Blocked):
						print("Blocked at pos {},{}".format(x,y))
					elif isinstance(self.content[x][y], NotABall):
						print("No Ball at pos {},{}".format(x,y))
					elif isinstance(self.content[x][y], Colored_Ball):
						print("Ball at pos {},{}".format(x,y))
					else:
						print("Problem at pos {},{}".format(x,y))
				self.content[x][y].draw(self.surf, (xcoord, ycoord))
			if debugprints:
				print("")
		# draw weightdisplay
		for x in range(1,9):
			#print(self.weights)
			weighttext = weightdisplayfont.render(str(self.weights[x-1]), True, (0,0,0))
			weightdisplay_x = weightdisplay_coords[0]
			weightdisplay_y = weightdisplay_coords[1]
			self.surf.blit(weighttext, (weightdisplay_x + (x-1)*weightdisplay_x_perCol, weightdisplay_y))
			
		return self.surf