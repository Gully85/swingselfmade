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
		content (10x9 array of either NotABall or Blocked or Balls). Leftmost and Rightmost 
			cols are all Blocked, as a dummy, to simplify boundaries. Second index counts y from 
			bottom (index=0) to highest position (index=7). At y=8 there should always be NotABall
		weights (8 ints, left to right). Keep in mind that content has a dummy row: weights[0] is 
			the total weight of all Balls in content[1][.]
		seesaws (4 ints, left to right). 0 indicates equal 
			weights, -1 for heavier left, +1 for heavier right).
		size (2 ints). Size of drawing are in px
		surf (pygame.Surface)
	Constructor takes size in pixels."""
	
	def __init__(self, size):
		self.content = [[ Blocked(),Blocked(),Blocked(),Blocked(), Blocked(),Blocked(),Blocked(),Blocked(),NotABall() ]]
		for i in range(8):
			self.content.append([ Blocked(),NotABall(),NotABall(),NotABall(), NotABall(),NotABall(),NotABall(),NotABall(),NotABall() ])
		self.content.append([ Blocked(),Blocked(),Blocked(),Blocked(), Blocked(),Blocked(),Blocked(),Blocked(),NotABall() ])
		
		self.weights = [0,0,0,0, 0,0,0,0]
		self.seesaws = [0,  0,   0,  0]
		self.size = size
		self.surf = Surface(size)
		self.changed = True # if anything changed since the last tick. Starts True so the initial gamestate is drawn.

	def check_alive(self):
		"""True if all topmost positions in self.content are NotABall. Player loses if any stack gets too high"""
		for x in range(1,9):
			if not isinstance(self.content[x][8], NotABall):
				return False
		return True
		
	def landBall(self, coords, ball, eventQueue):
		"""Land a ball at coords. Check for weight-moves, then for Scores, then for loss."""
		x,y = coords
		if isinstance(ball, Colored_Ball):
			self.content[x][y] = ball
			# check if a seesaw moves
			# keep in mind that indices in self.content[.][] are 1..8, so are x and neighbor,
			# all other content-array x indices are 0..7
			landingleft = (x%2 == 1)
			neighbor = x-1 + 2*landingleft
			weightx = self.weights[x-1] # excluding the just-landed ball
			weightneighbor = self.weights[neighbor-1]
			sesa = (x-1)//2 # can be 0..3, index in self.seesaws
			moving = False # if still False after the weight-moves checks, check for Scores

			# Three possible cases: Landing on the heavier side, landing on a (previously) 
			# balanced seesaw, landing on the (previously) lighter side.
			# y indices are 0..7. Exactly two of the bottom two of x+neighbor are Blocked, 
			# re-use the Blocked to reduce memory throughput
			if weightx > weightneighbor:
				pass
			elif weightx == weightneighbor:
				if ball.weight > 0:
					# move by one, throw highest neighbor Ball (if exists)
					moving = True
					# neighbor up by one
					for height in range(8, 0, -1):
						self.content[neighbor][height] = self.content[neighbor][height-1]
					self.content[neighbor][0] = self.content[x][0] 
					# landing stack down by one
					for height in range(0, y):
						self.content[x][height] = self.content[x][height+1]
					self.content[x][y] = NotABall()
					#TODO throw top ball of neighbor, if exists
					# seesaw was balanced, is now tilted towards landing side. -1 if landingleft, +1 else
					self.seesaws[sesa] = 1 - 2*landingleft 
					print("Seesaw state: ",self.seesaws)
				else:
					pass
			else:
				weightdiff = weightneighbor-weightx # is always positive
				if ball.weight < weightdiff:
					pass
				elif ball.weight == weightdiff:
					# move by one, set seesaw state to balanced
					moving = True
					# neighbor up by one
					for height in range(8,0,-1):
						self.content[neighbor][height] = self.content[neighbor][height-1]
					self.content[neighbor][0] = self.content[x][0]
					# landing stack down by one
					for height in range(0,y):
						self.content[x][height] = self.content[x][height+1]
					self.content[x][y] = NotABall()
					self.seesaws[sesa] = 0
					print("Seesaw state: ",self.seesaws)
				else:
					# move by two, flip seesaw state, throw highest neighbor Ball (it always exists)
					moving = True
					# neighbor up by two. TODO lose if neighbor stack is already 7 high
					for height in range(8, 1, -1):
						self.content[neighbor][height] = self.content[neighbor][height-2]
					# TODO throw highest ball on neighbor stack. It always exists.
					self.content[neighbor][1] = self.content[x][0]
					self.content[neighbor][0] = self.content[x][1]
					# landing stack down by two.
					for height in range(0, y-1):
						self.content[x][height] = self.content[x][height+2]
					self.content[x][y-1] = NotABall()
					self.content[x][y] = NotABall()
					self.seesaws[sesa] = - self.seesaws[sesa]
					print("Seesaw state: ",self.seesaws)
			if not moving:
				# check Scores
				pass

	def update_weights(self):
		"""calculate all weights, saves results in self.weights"""
		for x in range(1,9):
			sum=0
			for y in range(8):
				sum += self.content[x][y].weight
			self.weights[x-1]=sum
		
	#def update_seesaws(self):
	#	"""compares seesaw state with weights, update seesaws if necessary. Returns list of 4 Bools, True where state changed."""
	#	ret = [False, False, False, False]
	#	for sesa in range(4):
	#		left = 1 + sesa*2
	#		right= 2 + sesa*2
	#		
	#		if self.weights[left] > self.weights[right]:
	#			newstate = -1
	#		elif self.weights[left] == self.weights[right]:
	#			newstate = 0
	#		else:
	#			newstate = 1
	#		
	#		if newstate != self.seesaw[sesa]:
	#			ret[sesa] = True
	#			self.seesaw[sesa] = newstate
	#	return ret
		
	#def check_Scoring(self, coords):
	#	"""True if the Ball at the given coords should start a Scoring. It must be part of a horizontal 3-line for that."""
	#	x,y = coords
	#	content = self.content
	#	ball = content[x][y]
	#	color = ball.color
	#	# The ball itself has the correct color. Three possible cases: 
	#	# 1-Left and 2-Left have the correct color
	#	# 1-Left and 1-Right 
	#	# 1-Right and 2-Right
	#	# Difficulty: Can't access self.content[x-2] or [x+2] blindly, that would sometimes be out of array bounds.
	#	
	#	# catch the edge cases (coords are at the far-left or far-right) separately. If no edge case, [x-2] and [x+2]
	#	# can be accessed safely (might be Ball.Blocked objects with color=-1)
	#	
	#	#print("Entering scoring check at ",coords)
	#	if x == 1:
	#		#print("left edge, scored")
	#		return content[2][y].color == color and content[3][y].color == color
	#	elif x == 8:
	#		#print("right edge, scored")
	#		return content[7][y].color == color and content[6][y].color == color
	#	else:
	#		#print("colors of the 5 balls to check: ", content[x-2][y].color, content[x-1][y].color, content[x][y].color, #content[x+1][y].color, content[x+2][y].color)
	#		return (( content[x-2][y].color == color and content[x-1][y].color == color ) or
	#			   (  content[x-1][y].color == color and content[x+1][y].color == color ) or
	#			   (  content[x+1][y].color == color and content[x+2][y].color == color ))

	def check_Scoring_full(self):
		"""checks the full content for any horizontal-threes of the same color. 
		Returns (int,int) coords, leftmost ball, or [] if no horizontal-three is there.
		Checks bottom-up, only the lowest row with a horizontal-three is checked, only the leftmost Three is found.
		"""
		
		content = self.content
		# x range 1..8, y range 1..7 can have valid horizontal-threes
		for y in range(1,8):
			for x in range(1,7):
				color = content[x][y].color
				if color == -1:
					continue
				if content[x][y+1].color != color:
					continue
				if content[x][y+2].color == color:
					return (x,y)
		return []
		
		

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
						raise TypeError("In playfield at pos {},{} should be a Colored_Ball or NotABall or Blocked, instead there was {}.".format(x,y,self.content[x][y]))
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