# Scoring area, where the current level, number of dropped balls and Score is shown

from typing import Tuple
from pygame import Surface, font
import Balls
from Constants import ball_size

ballsdropped_font = font.SysFont("Arial", 16)
score_font = font.SysFont("Arial", 16)

class ScoreArea:
	"""Information about the score display area. Stores a local pygame.Surface. 
	Stores a Colored_Ball to draw the current level
	
	Vars:
		surf (pygame.Surface)
		size (int,int)
		changed (bool), True if redraw is needed
		levelball (Colored_Ball), whose draw() method is called on each redraw.
	Constructor: ScoreArea((size_x, size_y))
	"""
	
	
	
	def __init__(self, size: Tuple[int]):
		self.surf = Surface(size)
		self.size = size
		self.changed = True
		self.levelball = Balls.Colored_Ball(4, 4)
	
	def draw(self):
		from Game import level, balls_dropped, score
		self.surf.fill((127, 127, 127))
		
		# Level is at the top, as a Colored_Ball of the newest Color, with the level as weight
		
		# x position is a centered Colored_ball
		px_used = ball_size[0]
		level_position_x = 0.5*(self.size[0] - px_used)
		level_position_y = 0.1*self.size[1]
		level_position = (level_position_x, level_position_y)
		
		self.levelball.draw(self.surf, level_position)
		
		ballsdropped_text = ballsdropped_font.render("Balls dropped: " + str(balls_dropped), True, (0,0,0))
		ballsdropped_position_x = 0.1*self.size[0]
		ballsdropped_position_y = 0.4*self.size[1]
		ballsdropped_position = (ballsdropped_position_x, ballsdropped_position_y)
		self.surf.blit(ballsdropped_text, ballsdropped_position)
		
		score_text = score_font.render("Score: "+ str(score), True, (0,0,0))
		score_position_x = ballsdropped_position_x
		score_position_y = 0.8*self.size[1]
		score_position = (score_position_x, score_position_y)
		self.surf.blit(score_text, score_position)
		
		
		return self.surf
	
	def update_level(self):
		from Game import level
		self.levelball = Balls.Colored_Ball(level, level)
		