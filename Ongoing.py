# provides all possible ongoing events. Atm these are:
# - FallingBall. Ball that is lowering over time and soon landing
# - SeesawTilting. One of the four seesaws shifts position because weights have changed recently
# - Scoring. 3 horizontal are expanding, then remove the Balls and score points.

# all must have a .draw(surf) and a .tick(eventQueue, playfield) method.

import Balls as bal

from Constants import ballsize, playfield_ballcoord, playfield_ballspacing, scoring_delay

from Constants import falling_per_tick

class Ongoing:
	"""abstract Parent class, should not be instanciated"""
	pass

class FallingBall(Ongoing):
	"""a Ball that is being dropped, falling after being thrown, or the Ball below it vanished somehow. Vars:
		ball (Colored_Ball or Special_Ball)
		col (int, allowed range 1 <= col <= 8, matching the index in Playfield.content[.][])
		height (float, allowed range 8.0 >= height >= highest filled position in Playfield.content)
		
		Constructor: FallingBall(ball, col, starting_height=8.0). The starting height is optional, only to be used 
			if the Ball drops from Playfield instead of Crane/Thrown
		"""
	
	# Note to myself: Make sure that FallingBalls in the same col are at least 1.0 height apart
	
	def __init__(self, ball, col, starting_height=8.0):
		self.ball = ball
		self.col = col
		self.height = starting_height
		
	def draw(self, surf):
		x = playfield_ballcoord[0] + (self.col-1)*playfield_ballspacing[0]
		y = playfield_ballcoord[1] + (7.-self.height)*playfield_ballspacing[1]
		self.ball.draw(surf, (x,y))

	def tick(self, playfield, eventQueue):
		content = playfield.content
		new_height = int(self.height - falling_per_tick)
		playfield.changed=True
		if new_height > 7: #still higher in the air than where any playfield-Ball could be
			self.height -= falling_per_tick
		elif isinstance(content[self.col][new_height], bal.NotABall):
			self.height -= falling_per_tick
		else:
			print("reached Ground")
			x = self.col
			y = new_height+1 # index in content[][.]
			self.ball.land((x,y), playfield, eventQueue)
			eventQueue.remove(self)
			
		#content[x][y] = self.ball
		## check if the seesaw will stay in position. Only then can a Scoring start
		## columns are 1...8 (included). If x is even (check if x%2==0), the neighbor is x+1, else x-1
		## keep in mind that playfield.weights is off-by-one, index can be 0..7.
		#neighbor = x+1 - 2*(x%2 == 0)
		#neighborweight=playfield.weights[neighbor-1]
		#xstackweigh
		#if playfield.check_Scoring([x,y]):
		#	print("Scored!")
		#	eventQueue.append(Scoring([x,y], self.ball))
		#else:
		#	content[x][y] = self.ball
		#eventQueue.remove(self)
		#playfield.changed=True


class SeesawTilting(Ongoing):
	"""A seesaw that is shifting position over time. Vars:
		sesa (int, allowed values 0-3, from left to right. Tilting are columns 1+2*sesa and 2+2*sesa in theplayfield.content[.][])
		before (int, -1 or 0 or +1, seesaw state before tilting)
		after (int, -1 or 0 or +1, seesaw state after tilting). Must be different to before.
		progress (float, 0.0 to 1.0, counts up until tilt is finished)
	"""
	
	def __init__(self, sesa, before, after):
		self.sesa = sesa
		self.before = before
		self.after = after
		self.progress = 0.0
		
	def draw(self, surf):
		# TODO. Draw blocked areas partially, according to self.progress. 
		# Draw both stacks in current (moving) position over the already drawn stacks on surf. 
		pass


	def tick(self, eventQueue, playfield):
		# TODO
		pass


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
		# TODO put a placeholder. Different for past and present
		pass

	def tick(self, playfield, eventQueue):
		"""should be called once per tick. counts down delay, expands if zero was reached. If no expansion, removes this from the eventQueue"""
		#print(self, self.delay)
		self.delay -= 1
		if self.delay < 0:
			if self.expand(playfield, eventQueue):
				self.delay = scoring_delay
			else:
				eventQueue.remove(self)
				# TODO score and display

	def expand(self, playfield, eventQueue):
		"""checks if neighboring balls are same color, removes them and saves their coords in self.next for the next expand() call. Returns True if the Scoring grew.
		
		"""

		now = self.next
		self.next = []
		color = self.color
		#print("Expanding Scoring. Color=",color," past=",self.past, "now=",now)
		for coords in now:
			self.past.append(coords)
			x,y = coords
			playfield.content[x][y] = bal.NotABall()
			# removing a Ball may cause those on top to fall down
			if playfield.content[x][y+1].isBall and playfield.content[x][y+1].color != color:
				for ystack in range(y+1,8):
					eventQueue.append(FallingBall(playfield.content[x][ystack], x, starting_height=ystack))
					playfield.content[x][ystack] = bal.NotABall()
					if not playfield.content[x][ystack+1].isBall:
						break
			
			coords_to_check = [(x-1,y), (x+1,y), (x,y-1), (x,y+1)]
			for (x2,y2) in coords_to_check:
				if playfield.content[x2][y2].color == color:
					self.next.append([x2,y2])
					self.weight_so_far += playfield.content[x2][y2].weight
					playfield.content[x2][y2] = bal.NotABall()
					# removing a Ball may cause those on top to fall down
					if playfield.content[x2][y2+1].isBall and playfield.content[x2][y2+1].color != color:
						for ystack in range(y2+1,8):
							eventQueue.append(FallingBall(playfield.content[x2][ystack], x2, starting_height=ystack))
							playfield.content[x2][ystack] = bal.NotABall()
							if not playfield.content[x2][ystack+1].isBall:
								break

		#print("more matching Balls found: next=",self.next)
		if len(self.next) > 0:
			playfield.changed = True
			return True
		else:
			score = len(self.past) * self.weight_so_far
			print("Score from this: ",score)
			return False
		
