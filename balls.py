# provides the Balls classes

# A Ball can either be Colored (has weight, 3 horizontal can Score, 5 vertical can Combine). Parent class is Ball.
# or Special (weight=0, has effect when landing or ongoing effect while in Playfield). 

# Balls have a draw() method. Balls have a color attribute, for Scoring. color=-1 means colorless, never Scoring. The
# attribute isBall is True for ColoredBall and SpecialBall, and False for the placeholder-Dummys NotABall and
# Blocked.

from typing import Tuple
import colorschemes
import pygame
import random
from constants import ball_size

pygame.font.init()
ball_colors = colorschemes.simple_standard_ball_colors
text_colors = colorschemes.simple_standard_text_colors
ballfont = pygame.font.SysFont("monospace", 24)


# size of Balls in pixels. Is fix for now

class Ball:
    """Parent class for Colored and Special Balls. Abstract class, should not be instanciated."""
    pass


class NotABall(Ball):
    """Dummy class for places where there is no Ball. Empty Constructor."""
    # never change these globals, static vars for all NotABalls
    weight = 0
    color = -1
    isBall = False

    def __init__(self):
        pass

    def draw(self, surf: pygame.Surface, drawpos: Tuple[int,int]):
        pass


class Blocked(Ball):
    """Dummy class for positions blocked by the seesaw state"""
    # never change these globals, static var for all Blockeds
    weight = 0
    color = -1
    isBall = False

    def __init__(self):
        pass

    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]):
        # just a black rectangle for now
        pygame.draw.rect(surf, (0, 0, 0), pygame.Rect(drawpos, ball_size))


class Colored_Ball(Ball):
    """Child-class of Ball. Has a color (int, 1 <= color <= maxcolors) and a weight (int, 0 <= weight <= INT_MAX). Constructor is Colored_Ball(color, weight)."""
    # never change these globals, static var for all ColoredBalls
    isBall = True

    def __init__(self, color: int, weight: int):
        self.color = color
        self.weight = weight

    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]):
        """draws this Ball onto pygame.Surface surf to offset-position drawpos. Returns None"""
        color = ball_colors[self.color]
        pixelpos_rect = pygame.Rect(drawpos, ball_size)
        pygame.draw.ellipse(surf, color, pixelpos_rect, 0)
        weighttext = ballfont.render(str(self.weight), True, text_colors[self.color])
        posx = drawpos[0] + 0.2 * ball_size[0]
        posy = drawpos[1] + 0.2 * ball_size[1]
        surf.blit(weighttext, (posx, posy))
    
    def setweight(self, newweight: int):
        """sets the weight of the ball to given weight"""
        self.weight = newweight
    
    def getweight(self):
        """gets weight of the ball"""
        return self.weight


class Special_Ball(Ball):
    """Child-class of Ball. Has weight=0 and type (int, 0 < type <= 1, this will grow as more types are added).
	Types are (for now):
	0: Joker. Counts as any color for the purpose of Scoring a horizontal.
	1: Bomb. Upon landing, destroy all neighboring Balls (3x3 area centered on the Bomb spot). 
	Constructor is Special_Ball(type)"""
	# never change these globals, static vars for all ColoredBalls
    weight = 0  
    isBall = True

    def __init__(self, type: int):
        self.type = type

    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]):
        pass  # later, when Special_Balls are actually introduced


def generate_ball():
	import game
	
	# in the first 10 Balls of each level, the new color is more likely
	if game.balls_dropped % 50 < 10 and random.choice([True,False]):
		color = game.level
	else:
		color = random.randint(1, game.level)
	weight = random.randint(1, game.level)
	return Colored_Ball(color, weight)

def generate_starting_ball():
	color = random.randint(1, 4)
	weight = random.randint(1,4)
	return Colored_Ball(color, weight)