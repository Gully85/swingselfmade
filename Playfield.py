# provides the Playfield class. The playfield has 8 stacks of Balls 
# (lowest 0-2 are blocked, depending on seesaw state). An empty space in the playfield 
# is represented as None, same for a blocked space at the bottom.


debugprints = False

from typing import Tuple
from pygame import Rect, Surface, font
import Balls
from Balls import Blocked, NotABall, Colored_Ball, Special_Ball

import Ongoing
from Constants import playfield_ballcoord, playfield_ballspacing, weightdisplay_coords, weightdisplay_x_per_column
#from Ongoing import Scoring

#weightdisplayheight = 40
weightdisplayfont = font.SysFont("Arial", 12)

class Playfield:
	"""Information about the current Playfield. Variables:
		content (10x9 array of either NotABall or Blocked or Balls). Leftmost and Rightmost 
			columns are all Blocked, as a dummy, to simplify boundaries. Second index counts y from
			bottom (index=0) to highest position (index=7). At y=8 there should always be NotABall
		weights (8 ints, left to right). Keep in mind that content has a dummy row: weights[0] is 
			the total weight of all Balls in content[1][.]
		seesaws (4 ints, left to right). 0 indicates equal 
			weights, -1 for heavier left, +1 for heavier right).
		size (2 ints). Size of drawing are in px
		surf (pygame.Surface)
	Constructor takes size in pixels."""

	def __init__(self, size: Tuple[int]):
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
	
	def land_ball(self, coords: Tuple[int], ball):
		"""Land a ball at coords. Check for weight-moves, then for Scores, then for loss."""
		x,y = coords
		if isinstance(ball, Colored_Ball):
			self.content[x][y] = ball
			self.refresh_status()
		else:
			raise TypeError("Trying to land unexpected ball type ", ball, " at playfield position ", x, y)
	
	def refresh_status(self):
		"""Checks if anything needs to start now. Performs weight-check, 
		if that does nothing performs scoring-check, if that does nothing performs combining-check.
		"""
		if self.gravity_moves():
			return
		if self.check_Scoring_full():
			return
		if self.check_combining():
			return
		if self.check_hanging_balls():
			return
	
	def push_column(self, x: int, dy: int):
		"""pushes the x-column down by (dy) and its connected neighbor up by (dy)."""
		# x can be 1..8. Its neighbor is x-1 if x is even, and x+1 else.
		neighbor = x+1 - 2*(x%2 == 0)
		self.raise_column(neighbor, dy)
		self.lower_column(x, dy)

	def lower_column(self, x: int, dy: int):
		"""move all balls in a stack (dy) places down. """
		for height in range(0, 9-dy):
			self.content[x][height] = self.content[x][height + dy]
		# This will "duplicate" the NotABall on top of a stack. Is that a problem when 
		# it is later filled with an actual ball? I think not, but not 100% sure. A fix would be 
		# to create a new NotABall for y=8.

	def raise_column(self, x: int, dy: int):
		"""moves all balls in a stack (dy) places up. This can fill the highest place y=8 so the player loses."""
		for height in range(8, dy-1, -1):
			self.content[x][height] = self.content[x][height - dy]
		
		# the lowest 1 or 2 (depending on dy) become (newly-created) Blockeds. 
		# I let go of the old idea of re-using the Blockeds, code too ugly when 
		# not splitting this function into dy=1 and dy=2.
		for height in range(dy):
			self.content[x][height] = Blocked()

	def update_weights(self):
		"""calculate all weights, saves results in self.weights"""
		for x in range(1,9):
			sum = 0
			for y in range(8):
				sum += self.content[x][y].weight
			self.weights[x-1]=sum
	
	def gravity_moves(self):
		"""calculates all weights, compares with seesaw state, pushes if necessary, throws if necessary. 
		Returns True if any seesaw moved. Adds SeesawTilting and ThrownBall to the eventQueue if necessary.
		"""
		self.update_weights()
		ret = False
		for sesa in range(4):
			left = 2*sesa+1
			right = 2*sesa+2
			oldstate = self.seesaws[sesa]
			# self.weights is off-by-one due to the dummy row [0].
			if self.weights[left-1] > self.weights[right-1]:
				newstate = -1
			elif self.weights[left-1] == self.weights[right-1]:
				newstate = 0
			else:
				newstate = 1
			if newstate == oldstate:
				continue
			
			# if this point is reached, the seesaw must start moving now. There are 
			# three cases: Sided to balanced, balanced to sided, one-sided to other-sided. 
			Ongoing.tilt_seesaw(sesa, oldstate, newstate)
			self.seesaws[sesa] = newstate
			ret = True
			if newstate == 0:
				if oldstate == -1:
					self.push_column(right, 1)
				else:
					self.push_column(left, 1)
			elif newstate == -1:
				if oldstate == 0:
					self.push_column(left, 1)
				else:
					self.push_column(left, 2)
				# TODO throw top ball of right to the left. Distance is self.weights[left]-self.weights[right] (is always > 0)
				print("weight left=", self.weights[left-1], ", weight right=", self.weights[right-1])
				self.throw_top_ball(right, self.weights[right-1] - self.weights[left-1])
			else:
				if oldstate == 0:
					self.push_column(right, 1)
				else:
					self.push_column(right, 2)
				# TODO throw top ball of left to the right. Distance is self.weights[right]-self.weights[left] (is always > 0)
				print("weight left=", self.weights[left-1], ", weight right=", self.weights[right-1])
				self.throw_top_ball(left, self.weights[right-1] - self.weights[left-1])
			
		# when this point is reached, all seesaws have been checked and updated
		return ret
	
	def throw_top_ball(self, column: int, throwing_range: int):
		"""throw the top ball of column. If there is no ball, do nothing."""
		# throwing can only happen if the column is already the high side of a seesaw. Can safely 
		# assume that y=0 and y=1 are Blocked. Remove this sanity check once tests look good.
		from Game import GameStateError
		if not isinstance(self.content[column][0], Blocked) and isinstance(self.content[column][1], Blocked):
			raise GameStateError("Trying to throw from a non-lifted seesaw side, x=", column)
		lastball = self.content[column][2]
		if isinstance(lastball, NotABall):
			return
		
		for y in range(3, 8):
			ball = self.content[column][y]
			if isinstance(ball, Blocked):
				continue
			elif isinstance(ball, NotABall):
				Ongoing.throw_ball(lastball, (column, y-1), throwing_range)
				self.content[column][y-1] = NotABall()
				self.weights[column-1] -= self.content[column][y-1].weight
				return
			else:
				lastball = ball

	def check_Scoring_full(self):
		"""checks the full content for any horizontal-threes of the same color. 
		Adds a Scoring to the eventQueue if one was found.
		Returns True if a Scoring was found.
		Checks bottom-up, only the lowest row with a horizontal-three is checked, only the leftmost Three is found.
		"""
		
		print("Entering full scoring check")
		# x range 1..8, y range 1..7 can have valid horizontal-threes. These x,y loops look for the leftmost
		# Ball in a horizontal Three, so the x loop runs 1..6
		for y in range(1,8):
			for x in range(1,7):
				color = self.content[x][y].color
				if color == -1:
					continue
				#print("non-empty color at (", x, ",", y, ")")
				if self.content[x+1][y].color != color:
					continue
				#print("matching right neighbor (", x+1, ",", y, ")")
				if self.content[x+2][y].color == color:
					print("Found Scoring")
					Ongoing.eventQueue.append(Ongoing.Scoring((x,y), self.content[x][y]))
					return True
		return False

	def check_hanging_balls(self):
		"""checks the full playfield for balls that 'hang', i.e. no ball/Blocked below them.
		Convert them all into FallingBalls. Returns True if any were converted."""
		
		ret = False
		for x in range(1,9):
			# search highest position that can support a ball
			for y in range(0,8):
				current = self.content[x][y]
				if current.isBall:
					continue
				elif isinstance(current, Blocked):
					continue
				elif isinstance(current, NotABall):
					air_height = y
					break
				else:
					raise TypeError("in hanging-Balls check: Unexpected ball type ", current, "  at position ", x, y)
			
			for y in range(air_height, 8):
				current = self.content[x][y]
				if current.isBall:
					ret = True
					Ongoing.eventQueue.append(Ongoing.FallingBall(current, x, starting_height=y))
					self.content[x][y] = NotABall()
		
		return ret

	def check_combining(self):
		"""Checks the full gameboard for vertical Fives. Only one per stack is possible. 
		Combines if one is found, and creates an Ongoing.Combining. Returns True if any are found"""
		# feels like this could be written easier. Especially the thing in the check_height loop. 
		# @Chris, do you have an idea?
		ret = False
		
		print("Entering full Combining check")
		for x in range(1,9):
			for y in range(0, 4):
				this_color = self.content[x][y].color
				if this_color == -1:
					continue
				# if this point is reached, the current ball is a Colored_Ball. All others have the 
				# attribute color==-1
				total_weight = self.content[x][y].weight
				
				# five balls are needed: y, y+1, ..., y+4. If this loop reaches y+5, do not check 
				# the (y+5)-position, but Combine instead
				for check_height in range(y, y+6):
					if check_height == y+5:
						ret = True
						self.content[x][y] = Colored_Ball(this_color, total_weight)
						Ongoing.eventQueue.append(Ongoing.Combining((x,y), this_color, total_weight))
						self.content[x][y+1] = NotABall()
						self.content[x][y+2] = NotABall()
						self.content[x][y+3] = NotABall()
						self.content[x][y+4] = NotABall()
					
					if self.content[x][check_height].color != this_color:
						break 
					
					total_weight += self.content[x][check_height].weight
		
		if (ret):
			self.check_hanging_balls()
		
		return ret
		
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
			self.surf.blit(weighttext, (weightdisplay_x + (x-1) * weightdisplay_x_per_column, weightdisplay_y))
			
		return self.surf