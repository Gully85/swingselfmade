# provides the Balls classes

# "Grandparent" class is PlayfieldSpace. This can be an EmptySpace
# or a Ball. 
# Ball is an abstract Parent class, can be ColoredBall or SpecialBall
# 
# EmptySpace is not abstract, but BlockedSpace inherits from it. BlockedSpace
# is a position blocked by the seesaw state, can only be in the lowest two 
# positions of the playfield.

from __future__ import annotations
from typing import Tuple
import colorschemes
import pygame
import random
from constants import ball_size, pixel_coord_in_playfield
from abc import ABC, abstractmethod
import game

pygame.font.init()
ball_colors = colorschemes.simple_standard_ball_colors
text_colors = colorschemes.simple_standard_text_colors
ballfont = pygame.font.SysFont("monospace", 24)


class PlayfieldSpace(ABC):
    """Abstract Base Class for a position in the playfield. It can either be a ball 
    (whatever kind) or an EmptySpace or BlockedSpace. (BlockedSpace means, blocked by 
    seesaw). Must have draw(), getweight() and getcolor() methods."""
    
    @abstractmethod
    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]):
        """draw yourself on given surf to given pixel position"""
        pass

    @abstractmethod
    def getweight(self):
        pass

    @abstractmethod
    def getcolor(self): 
        pass

    @abstractmethod
    def matches_color(self, ball: Ball):
        return False
    
    @abstractmethod
    def is_scoring(self):
        return False

class EmptySpace(PlayfieldSpace):
    """Dummy class for places where there is no Ball. Empty Constructor."""

    def __init__(self):
        pass

    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]):
        pass

    def getweight(self):
        return 0
    
    def getcolor(self):
        return -1
    
    def matches_color(self, ball: Ball):
        return False
    
    def is_scoring(self):
        return False

class BlockedSpace(PlayfieldSpace):
    """Dummy class for positions blocked by the seesaw state"""

    def __init__(self):
        pass

    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]):
        # just a black rectangle for now
        pygame.draw.rect(surf, (0, 0, 0), pygame.Rect(drawpos, ball_size))
    
    def getweight(self):
        return 0
    
    def getcolor(self):
        return -1
    
    def matches_color(self, ball: Ball):
        return False
    
    def is_scoring(self):
        return False

class Ball(PlayfieldSpace):
    """Abstract class indicating that in this space is a ball. Can be either a ColoredBall 
    or a SpecialBall."""

    @abstractmethod
    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]):
        pass
    
    @abstractmethod
    def getweight(self):
        return 0

    @abstractmethod
    def getcolor(self):
        return -1
    
    @abstractmethod
    def matches_color(self, ball: Ball):
        return False
    
    @abstractmethod
    def is_scoring(self):
        """True if the Ball has been marked by an expanding Scoring"""
        return False

class ColoredBall(Ball):
    """Child-class of Ball. Has a color (int, 1 <= color <= maxcolors)
    and a weight (int, 0 or greater). Constructor is Colored_Ball(color, weight)."""

    def __init__(self, color: int, weight: int):
        self.color = color
        self.weight = weight
        self.scoring = False

    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]):
        """draws this Ball onto pygame.Surface surf to offset-position drawpos. Returns None"""
        color = ball_colors[self.color]
        
        pixelpos_rect = pygame.Rect(drawpos, ball_size)
        pygame.draw.ellipse(surf, color, pixelpos_rect, 0)
        if self.is_scoring():
            pastcolor = (65,174,118) # for currently scoring balls
            pygame.draw.ellipse(surf, pastcolor, pixelpos_rect, 3)
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
    
    def setcolor(self, newcolor: int):
        self.color = newcolor

    def getcolor(self):
        return self.color

    def matches_color(self, ball: Ball):
        # TODO Joker
        if not isinstance(ball, ColoredBall):
            return False
        return ball.getcolor() == self.color
    
    def mark_for_scoring(self):
        """Converts Ball to ScoringColoredBall, returns new one"""
        self.scoring = True
    
    def is_scoring(self):
        return self.scoring


class SpecialBall(Ball):
    """abstract class. Must be instanciated as one of the SpecialBall types. These all have weight==0.
    Must implement draw(surf, drawpos) and land_on_bottom(coords) and land_on_ball(coords)."""

    @abstractmethod
    def __init__(self):
        pass
    
    def getweight(self):
        return 0
    
    def getcolor(self):
        return -1

    @abstractmethod
    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]):
        surf.blit(self.image, drawpos)
        # somehow make sure that self.image exists. @property decorator?

    @abstractmethod
    def landing_effect_on_ground(self, coords: Tuple[int]):
        pass

    @abstractmethod
    def landing_effect_on_ball(self, coords: Tuple[int]):
        pass

    @abstractmethod
    def matches_color(self, ball: Ball):
        return False

    def is_scoring(self):
        """Most SpecialBalls can not score, so False is the default answer. 
        This is overriden in the exceptions: Heart and Star"""
        return False

class Bomb(SpecialBall):
    """Special Ball. If landing on a Ball, it explodes a 3x3 area. If landing on a BlockedSpace, it
    just lies around, but explodes once any Ball lands on it or a neighboring Bomb explodes."""

    level_required = 4

    def __init__(self):
        self.image = pygame.image.load("specials/bombe-selbstgemalt.png")

    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]):
        super().draw(surf, drawpos)

    def landing_effect_on_ground(self, coords: Tuple[int]):
        pass

    def landing_effect_on_ball(self, coords: Tuple[int]):
        self.explode(coords)

    def explode(self, coords: Tuple[int]):
        the_playfield = game.playfield
        # TODO in 3x3 area: Display explosion sprite (ongoing), explode bombs, remove other balls
        xcenter,ycenter = coords
        game.ongoing.draw_explosion(coords)

        the_playfield.remove_ball(coords)

        for x in range(xcenter-1, xcenter+2):
            if x < 0 or xcenter > 7:
                continue
            for y in range(ycenter-1, ycenter+2):
                if y < 0 or y > 7:
                    continue
                ball_there = the_playfield.get_ball_at((x,y))
                if isinstance(ball_there, Bomb):
                    ball_there.explode((x,y))
                elif isinstance(ball_there, Ball):
                    the_playfield.remove_ball((x,y))

        the_playfield.refresh_status()
    
    def matches_color(self, ball: Ball):
        return False

class Cutter(SpecialBall):
    """Special Ball. Destroys the stack it lands on. Once hitting the BlockedSpace or
    height 0, it disappears."""

    level_required = 5

    def __init__(self):
        self.image = pygame.image.load("specials/bohrer-selbstgemalt.png")
    
    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]):
        super().draw(surf, drawpos)
    
    def landing_effect_on_ground(self, coords: Tuple[int]):
        game.playfield.remove_ball(coords)

    def landing_effect_on_ball(self, coords: Tuple[int]):
        x,y = coords
        game.playfield.remove_ball((x, y-1))
        game.playfield.remove_ball(coords)
        game.ongoing.ball_falls_from_height(self, x, y)
    
    def matches_color(self, ball: Ball):
        return False

class Heart(SpecialBall):
    """No special effects. When Scoring, this will increase the global 
    score factor by 0.1*(number of Hearts scored)"""

    level_required = 4

    def __init__(self):
        self.image = pygame.image.load("specials/Herz-selbstgemalt.png")
        self.scoring = False
    
    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]):
        super().draw(surf, drawpos)
        
    def landing_effect_on_ground(self, coords: Tuple[int]):
        pass

    def landing_effect_on_ball(self, coords: Tuple[int]):
        pass

    def matches_color(self, ball: Ball):
        return isinstance(ball, Heart) # for now. TODO Joker
    
    def mark_for_Scoring(self):
        self.scoring = True
    
    def is_scoring(self):
        return self.scoring

nextspecial = Bomb()
nextspecial_delay = 5

def regenerate_nextspecial():
    """Resets the upcoming special and timer
    to new randomly generated ones"""
    import game

    random_pool = [Bomb, Cutter, Heart]
    pick = random.choice(random_pool)
    while pick.level_required > game.level:
        pick = random.choice(random_pool)
    
    global nextspecial, nextspecial_delay
    nextspecial = pick()
    nextspecial_delay = random.randint(int(0.8*pick.level_required), int(1.2*pick.level_required))
    if nextspecial_delay < 6:
        nextspecial_delay = 6
    #print("next upcoming Special: " + pick + " in " + nextspecial_delay)

def generate_ball():
    import game

    # TODO Star at levelup

    global nextspecial_delay
    if nextspecial_delay == 0:
        ret = nextspecial
        regenerate_nextspecial()
        return ret
    nextspecial_delay -= 1
    
    # in the first 10 Balls of each level, the new color is more likely
    if game.balls_dropped % 50 < 10 and random.choice([True,False]):
        color = game.level
    else:
        color = random.randint(1, game.level)
    weight = random.randint(1, game.level)
    return ColoredBall(color, weight)

def generate_starting_ball():
    """This will always generate a ColoredBall."""
    color = random.randint(1, 4)
    weight = random.randint(1,4)
    return ColoredBall(color, weight)

def force_special(char):
    """Forces the next generated ball to be a Bomb/Cutter/Heart,
    depending on char being B/C/H. If not B/C/H, do nothing"""
    global nextspecial, nextspecial_delay
    if char == "B":
        nextspecial = Bomb()
    elif char == "C":
        nextspecial = Cutter()
    elif char == "H":
        nextspecial = Heart()
    else:
        return
    nextspecial_delay = 1
    