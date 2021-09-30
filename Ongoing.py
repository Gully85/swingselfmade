# provides all possible ongoing events. Atm these are:
# - FallingBall. Ball that is lowering over time and soon landing
# - SeesawTilting. One of the four seesaws shifts position because weights have changed recently
# - Scoring. 3 horizontal are expanding, then remove the Balls and score points.

# all must have a .draw(surf) and a .tick(playfield) method.

# shorts:
# - drop_ball(ball, column) to drop a ball from crane-height
# - tilt_seesaw(seesaw, before, after) to move a seesaw from a position to another
# - throw_ball(ball, origin_coords, throwing_range) to throw a ball. Positive throwing_range indicates 
# throwing to the right, to higher x-values / columns

import Balls

from Constants import ball_size, playfield_ballcoord, playfield_ballspacing
from Constants import falling_per_tick, tilting_per_tick, scoring_delay, rising_per_tick, sideway_per_tick
from Constants import throwing_height

# this is a local variable of the "module" Ongoing. Other files, if they import Ongoing,
# can use and modify this. Their local name is Ongoing.eventQueue
eventQueue = []

class Ongoing:
	"""abstract Parent class, should not be instanciated"""
	pass

class FallingBall(Ongoing):
	"""a Ball that is being dropped, falling after being thrown, or the Ball below it vanished somehow. Vars:
		ball (Colored_Ball or Special_Ball)
		column (int, allowed range 1 <= column <= 8, matching the index in Playfield.content[.][])
		height (float, allowed range 8.0 >= height >= highest filled position in Playfield.content in respective column)
		
		Constructor: FallingBall(ball, col, starting_height=8.0). The starting height is optional, only to be used 
			if the Ball drops from Playfield instead of Crane/Thrown
		"""
	
	def __init__(self, ball, column, starting_height=8.0):
		self.ball = ball
		self.column = column
		self.height = starting_height
		
	def draw(self, surf):
		x = playfield_ballcoord[0] + (self.column - 1) * playfield_ballspacing[0]
		y = playfield_ballcoord[1] + (7.-self.height)*playfield_ballspacing[1]
		self.ball.draw(surf, (x,y))

	def tick(self, playfield):
		content = playfield.content
		new_height = int(self.height - falling_per_tick)
		playfield.changed = True
		if new_height > 7: #still higher in the air than where any playfield-Ball could be
			self.height -= falling_per_tick
		elif isinstance(content[self.column][new_height], Balls.NotABall):
			self.height -= falling_per_tick
		else:
			x = self.column
			y = new_height+1 # index in content[][.]
			eventQueue.remove(self)
			playfield.land_ball((x, y), self.ball)

def drop_ball(ball, column):
	eventQueue.append(FallingBall(ball, column))

class ThrownBall(Ongoing):
	"""A ball that was thrown by a seesaw. Moves up, then sideways to the correct column, then becomes a FallingBall. Vars:
		ball (Colored_Ball or Special_Ball)
		column (float, not int), allowed range 1.0 <= column <= 8.0. Current position x
		height (float), allowed range 1.0 <= height <= 9.0. Current position y
		throwing_range (float), all values possible. How far will this be thrown sideways, in columns. 
			Positive values indicate throwing to the right, negative to the left.
		Constructor: ThrownBall(ball, (x,y), throwingRange), x and y and throwingRange should all be ints
		"""
	
	def __init__(self, ball, coords, throwing_range):
		self.ball = ball
		self.column = float(coords[0])
		self.height = float(coords[1])
		self.throwing_range = float (throwing_range)
	
	def draw(self, surf):
		# identical to FallingBall.draw() so far
		x = playfield_ballcoord[0] + (self.column-1)*playfield_ballspacing[0]
		y = playfield_ballcoord[0] + (7. - self.height)*playfield_ballspacing[1]
		self.ball.draw(surf, (x,y))
		
	def tick(self, playfield):
		# up until self.height==9.0, then sideways until throwingRange==0, then become a FallingBall
		# The whole out-of-bounds and convert-to-Bomb/Heart mechanic does not
		# exist yet. For now, just discard anything that leaves the bounds. 
		# Discard when column < 0.5 or column > 8.5
		playfield.changed=True
		if self.height < 8.5:
			self.height += rising_per_tick
			return
		elif self.height > throwing_height:
			self.height = throwing_height
			print("ThrownBall reached final height")
		
		if self.throwing_range > 0.0:
			self.column += sideway_per_tick
			self.throwing_range -= sideway_per_tick
			if self.throwing_range <= 0.0:
				eventQueue.append(FallingBall(self.ball, int(self.column+0.5), starting_height=throwing_height-1.0))
				eventQueue.remove(self)
		else:
			self.column -= sideway_per_tick
			self.throwing_range += sideway_per_tick
			if self.throwing_range >= 0.0:
				eventQueue.append(FallingBall(self.ball, int(self.column+0.5), starting_height=throwing_height-1.0))
				eventQueue.remove(self)
				print("removing ThrownBall, converting to FallingBall")
		
		if self.column < 0.5 or self.column > 8.5:
			eventQueue.remove(self)
			print("removing ThrownBall, sideway out-of-bounds")

def throw_ball(ball, origin_coords, throwing_range):
	eventQueue.append(ThrownBall(ball, origin_coords, throwing_range))
	print("throwing Ball, ", ball, origin_coords, throwing_range)

class SeesawTilting(Ongoing):
	"""A seesaw that is shifting position over time. Vars:
		sesa (int, allowed values 0-3, from left to right. Tilting are columns 1+2*sesa and 2+2*sesa in theplayfield.content[.][])
		before (int, -1 or 0 or +1, seesaw state before tilting)
		after (int, -1 or 0 or +1, seesaw state after tilting). Must be different to before.
		progress (float, 0.0 to 1.0, counts up until tilt is finished)

		Constructor: SeesawTilting(sesa, before, after, playfield, eventQueue).
		When the Constructor is called, it will put the playfield.content columns in the positions of the final state. If needed, it will throw the top Ball and create&add a ThrownBall to the eventQueue
	"""

	def __init__(self, sesa, before, after):
		self.sesa = sesa
		self.before = before
		self.after = after
		self.progress = 0.0
		if before == after:
			raise ValueError("can not tilt seesaw ",sesa," from position ", before," to the same one.")
		
	def draw(self, surf):
		# TODO. Draw blocked areas partially, according to self.progress. 
		# Draw both stacks in current (moving) position over the already drawn stacks on surf. 
		pass

	def tick(self, playfield):
		self.progress += tilting_per_tick
		playfield.changed = True
		if self.progress >= 1.0:
			eventQueue.remove(self)
			playfield.refresh_status()

def tilt_seesaw(seesaw, before, after):
	eventQueue.append(SeesawTilting(seesaw, before, after))
	print("tilting seesaw, ", seesaw, before, after)

class Scoring(Ongoing):
	"""Balls currently scoring points. Vars:
		past (list of [int,int], refers to coords in Playfield.content). Coords of all Balls that were already scored
		next (list of [int,int], refers to coords in Playfield.content). Coords of all Balls that should check their neighbors at next expand().
		color (int, corresponds to Ball.color)
		delay (int, counting down from scoring_delay. Number of ticks until Scoring will expand next)
		weight_so_far (int)
		
		Constructor: Scoring((x,y), ball)
	"""
	
	def __init__(self, coords, ball):
		self.past = []
		self.next = [coords]
		self.color = ball.color
		#print("New Scoring, color=",self.color)
		self.delay = scoring_delay
		self.weight_so_far = ball.weight
		
	def draw(self, surf):
		# TODO put a placeholder for each removed Ball. Maybe a different one for past and present
		pass

	def tick(self, playfield):
		"""called once per tick. Counts down delay, expands if zero was reached, and reset delay. 
		If no expansion, removes this from the eventQueue
		"""
		#print(self, self.delay)
		self.delay -= 1
		if self.delay < 0:
			if self.expand(playfield):
				self.delay = scoring_delay
			else:
				# Formula for Scores: Total weight x number of balls x level (level does not exist yet)
				print("Score from this: ", self.weight_so_far * len(self.past))
				eventQueue.remove(self)
				playfield.refresh_status()
				# TODO score and display

	def expand(self, playfield):
		"""checks if neighboring balls are same color, removes them and saves their coords in self.next for the next expand() call. Returns True if the Scoring grew.
		
		"""

		now = self.next
		self.next = []
		color = self.color
		#print("Expanding Scoring. Color=",color," past=",self.past, "now=",now)
		for coords in now:
			self.past.append(coords)
			x,y = coords
			playfield.content[x][y] = Balls.NotABall()
			# removing a Ball may cause those on top to fall down
			if playfield.content[x][y+1].isBall and playfield.content[x][y+1].color != color:
				for ystack in range(y+1,8):
					eventQueue.append(FallingBall(playfield.content[x][ystack], x, starting_height=ystack))
					playfield.content[x][ystack] = Balls.NotABall()
					if not playfield.content[x][ystack+1].isBall:
						break
			
			coords_to_check = [(x-1,y), (x+1,y), (x,y-1), (x,y+1)]
			for (x2,y2) in coords_to_check:
				if playfield.content[x2][y2].color == color:
					self.next.append([x2,y2])
					self.weight_so_far += playfield.content[x2][y2].weight
					playfield.content[x2][y2] = Balls.NotABall()
					# removing a Ball may cause those on top to fall down
					if playfield.content[x2][y2+1].isBall and playfield.content[x2][y2+1].color != color:
						for ystack in range(y2+1,8):
							eventQueue.append(FallingBall(playfield.content[x2][ystack], x2, starting_height=ystack))
							playfield.content[x2][ystack] = Balls.NotABall()
							if not playfield.content[x2][ystack+1].isBall:
								break

		#print("more matching Balls found: next=",self.next)
		playfield.changed = True
		return len(self.next) > 0
		#if len(self.next) > 0:
		#	playfield.changed = True
		#	return True
		#else:
		#	#score = len(self.past) * self.weight_so_far
		#	#print("Score from this: ",score)
		#	return False
		
