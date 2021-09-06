# provides all possible ongoing events. Atm these are:
# - FallingBall. Ball, int col (1 through 8, matching index in Playfield.content[.]), float height

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
	
	def __init__(self, ball, column, starting_height=8.0):
		self.ball = ball
		self.column = column
		self.height = starting_height
		
	def draw(self, surf):
		x = playfield_ballcoord[0] + (self.column-1)*playfield_ballspacing[0]
		y = playfield_ballcoord[1] + (7.-self.height)*playfield_ballspacing[1]
		self.ball.draw(surf, (x,y))
		
	def tick(self, eventQueue, playfield):
		content = playfield.content
		new_height = int(self.height - falling_per_tick)
		if new_height > 7: #still higher in the air than where any playfield-Ball could be
			self.height -= falling_per_tick
			playfield.changed=True
		elif isinstance(content[self.column][new_height], bal.NotABall):
			self.height -= falling_per_tick
			playfield.changed=True
		else:
			print("reached Ground")
			x = self.column
			y = new_height+1 # index in content[][.]
			content[x][y] = self.ball
			# check Scoring
			eventQueue.remove(self)
			playfield.changed=True

		#	if isinstance(event, ong.FallingBall):
		#		#print(event.col, event.height, falling_per_tick)
		#		# check if hitting ground in this tick
		#		new_height = int(event.height - falling_per_tick)
		#		if new_height > 7: #still higher in the air than where any playfield-Ball could be
		#			event.height -= falling_per_tick
		#			the_playfield.changed=True
		#		elif isinstance(the_playfield.content[event.col][new_height], bal.NotABall):
		#			event.height -= falling_per_tick
		#			the_playfield.changed=True
		#		else:
		#			print("reached Ground")
		#			x = event.col
		#			y = new_height+1 # index in the_playfield.content[][.]
		#			the_playfield.content[x][y] = event.ball
		#			if the_playfield.check_Scoring([x, y]):
		#				ongoing_Events.append(ong.Scoring((x,y), event.ball))
		#			the_playfield.changed=True
		#			ongoing_Events.remove(event)		
		
		
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
		coords (list of [int,int] coords in theplayfield.content)
		color (int, corresponds to Ball.color)
		balls_so_far (int)
		totalweight_so_far (int)
		delay (int, counting down from scoring_delay. Number of ticks until Scoring will expand next)
		
		Constructor: Scoring((x,y), ball)
	"""
	
	def __init__(self, coords, ball):
		self.coords = [coords]
		self.color = ball.color
		self.balls_so_far = 1
		self.totalweight_so_far = ball.weight
		self.delay = scoring_delay
		
	def draw(self, surf):
		# TODO
		pass

	def tick(self, eventQueue, playfield):
		pass

	def expand(self, content):
		# TODO
		pass
