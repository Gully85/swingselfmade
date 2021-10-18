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
from pygame import Surface

from Constants import ball_size, playfield_ballcoord, playfield_ballspacing
from Constants import falling_per_tick, tilting_per_tick, scoring_delay
from Constants import thrown_ball_dropheight


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
	
	def __init__(self, ball, column: int, starting_height=8.0):
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

def drop_ball(ball, column: int):
	eventQueue.append(FallingBall(ball, column))

class ThrownBall(Ongoing):
	"""A ball that was thrown by a seesaw. Follows a certain trajectory 
		(see comment in tick() for details), then becomes a FallingBall. Vars:
		ball (Colored_Ball or Special_Ball).
		destination (int), allowed range 0 <= destination <= 9. Values 1..8 indicate landing in that column,
			Values 0 or 9 indicate flying out sideway. Destination height is always 8.2
		origin (int,int tuple), x and y coordinate of the spot from where it was launched. 1 <= x <= 8. 
			If it came in flying from the side, x = 0 or 9 and y = 7.
		x (float, not int), allowed range 1.0 <= column <= 8.0. Current position.
		y (float), allowed range 1.0 <= height <= 9.0. Current position.
		remaining_range (int), all values possible. Value is 0 except when it will be thrown out sideway, 
			in which case it is the remaining number of columns to be thrown. Not to be confused with the 
			constructor argument throwing_range. This is the remaining number of columns after the next fly-out,
			the constructor argument is the total number of columns to fly. Negative if flying to the left
		t (float), running parameter for the trajectory. Values -1 <= t <= +1
		
		
		Constructor: ThrownBall(ball, (x,y), throwing_range), x and y and throwing_range should all be ints. 
		Positive throwing_range indicates throwing to the right, negative to the left
		"""
	
	def __init__(self, ball, coords: (int, int), throwing_range: int):
		self.ball = ball
		self.origin = coords
		self.x = float(coords[0])
		self.y = float(coords[1])
		if throwing_range == 0:
			raise ValueError("Attempting to throw ball ", ball, " from position ", coords, " with range zero.")
		
		# calculate destination. Three possible cases: Flying out left, landing in-bound, flying out right.
		destination_raw = coords[0] + throwing_range
		if destination_raw < 1: # fly out left
			self.destination = 0
			self.remaining_range = destination_raw
		elif destination_raw > 8: # fly out right
			self.destination = 9
			self.remaining_range = destination_raw - 8
		else: # stay in-bound
			self.destination = destination_raw
			self.remaining_range = 0
		
		# the trajectory is parametrized with t going from -1 to +1
		self.t = -1
		
		print("Throwing ball ", ball, " from position ", coords, " with range ",
				throwing_range, ". Destination is ", self.destination, ", remaining is ", self.remaining_range)
		
		# Maybe generate the trajectory here, as a local lambda(t)?
		
	def draw(self, surf):
		# identical to FallingBall.draw() so far
		x = playfield_ballcoord[0] + (self.x-1)*playfield_ballspacing[0]
		y = playfield_ballcoord[0] + (7. - self.y)*playfield_ballspacing[1]
		self.ball.draw(surf, (x,y))
		
	def tick(self, playfield):
		# increase t. If destination was reached (t>1), convert into a FallingBall or perform the fly-out.
		# If not, calculate new position x,y from the trajectory.
		from Constants import thrown_ball_dt , thrown_ball_maxheight
		
		self.t += thrown_ball_dt
		playfield.changed=True
		
		# is the destination reached? If yes, it can become a FallingBall or it can fly out
		if self.t > 1.0:
			if self.destination == 0 or self.destination == 9:
				self.fly_out(self.destination == 0)
			else:
				eventQueue.append(FallingBall(self.ball, self.destination, starting_height=thrown_ball_dropheight-2.0))
				eventQueue.remove(self)
		else:
			# Ball has not reached its destination yet. Update x and y of the trajectory.
			# The trajectory is a standard parabola -t**2. The t<0 side is for origin to max, 
			# t>0 arm for max to destination. t=-1 is origin, t=0 is max, t=1 is destination.
			# max is always at x=(origin+destination)/2, y=thrown_ball_maxheight
			# (That implies that the derivative is not smooth at the max. So be it.)
			maxx = (self.origin[0] + self.destination)/2
			maxy = thrown_ball_maxheight
			
			if self.t < 0.0:
				# t<0 origin side: t=0 is (maxx, maxy), t=-1 is origin
				self.x = maxx + self.t *  (maxx - self.origin[0])
				self.y = maxy - self.t**2*(maxy - self.origin[1])
			else:
				# t>0 destination side: Same thing with destination instead of origin
				self.x = maxx - self.t *  (maxx - self.destination)
				self.y = maxy - self.t**2*(maxy - thrown_ball_dropheight)
				
	
	def fly_out(self, left: bool):
		"""Ball flew out to the left or right (indicated by argument). Insert it at the
			very right/left, set new origin, calculate and set new destination
		"""
		from Constants import thrown_ball_flyover_height
		self.t = -1.0
		self.y = thrown_ball_flyover_height
		if left:
			self.x = 9.0
		else:
			self.x = 0.0
		self.origin = (self.x, self.y)
		# calculate new destination. It can be another fly-out (if remaining_range is high enough) or a column.
		# Didn't find a way to make this shorter without losing readability...
		if left:
			if self.remaining_range < -7:
				self.destination = 0
				self.remaining_range += 8
			else:
				self.destination = 8 + self.remaining_range  # self.remaining is negative
				self.remaining_range = 0
		else:
			if self.remaining_range > 7:
				self.destination = 9
				self.remaining_range -= 8
			else:
				self.destination = self.remaining_range
				self.remaining_range = 0
		
		print("Ball flying out, left=", left, ", new remaining_range=", self.remaining_range, 
			" and destination=", self.destination)

def throw_ball(ball, origin_coords: (int, int), throwing_range: int):
	eventQueue.append(ThrownBall(ball, origin_coords, throwing_range))
	# print("throwing Ball, ", ball, origin_coords, throwing_range)

class SeesawTilting(Ongoing):
	"""A seesaw that is shifting position over time. Vars:
		sesa (int, allowed values 0-3, from left to right. Tilting are columns 1+2*sesa and 2+2*sesa in theplayfield.content[.][])
		before (int, -1 or 0 or +1, seesaw state before tilting)
		after (int, -1 or 0 or +1, seesaw state after tilting). Must be different to before.
		progress (float, 0.0 to 1.0, counts up until tilt is finished)

		Constructor: SeesawTilting(sesa, before, after, playfield, eventQueue).
	"""

	def __init__(self, sesa: int, before: int, after: int):
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

def tilt_seesaw(seesaw: int, before: int, after: int):
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
	
	def __init__(self, coords: (int, int), ball):
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
		
		import Game
		self.delay -= 1
		if self.delay < 0:
			if self.expand(playfield):
				self.delay = scoring_delay
			else:
				# Formula for Scores: Total weight x number of balls x level (level does not exist yet)
				print("Score from this: ", self.weight_so_far * len(self.past) * Game.level)
				Game.score += self.weight_so_far * len(self.past) * Game.level
				print("Total score: ", Game.score)
				Game.score_area.changed = True
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
		
