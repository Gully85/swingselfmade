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

class ColoredBall(Ball):
    """Child-class of Ball. Has a color (int, 1 <= color <= maxcolors)
    and a weight (int, 0 or greater). Constructor is Colored_Ball(color, weight)."""

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
    
    def setcolor(self, newcolor: int):
        self.color = newcolor

    def getcolor(self):
        return self.color

    def matches_color(self, ball: Ball):
        # TODO Joker
        if not isinstance(ball, ColoredBall):
            return False
        return ball.getcolor() == self.color
    
    def mark_for_Scoring(self):
        """Converts Ball to ScoringColoredBall, returns new one"""
        return ScoringColoredBall(self.getcolor(), self.getweight())

class ScoringColoredBall(ColoredBall):
    def draw(self, surf: pygame.Surface, drawpos: Tuple[int,int]):
        super().draw(surf, drawpos)
        pastcolor = (65,174,118)
        pygame.draw.rect(surf, pastcolor, pygame.Rect(pixel_coord_in_playfield(drawpos), ball_size), width=3)


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

class Bomb(SpecialBall):
    """Special Ball. If landing on a Ball, it explodes a 3x3 area. If landing on a BlockedSpace, it
    just lies around, but explodes once any Ball lands on it or a neighboring Bomb explodes."""

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

    def __init__(self):
        self.image = pygame.image.load("specials/Herz-selbstgemalt.png")
    
    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]):
        super().draw(surf, drawpos)
    
    def landing_effect_on_ground(self, coords: Tuple[int]):
        pass

    def landing_effect_on_ball(self, coords: Tuple[int]):
        pass

    def matches_color(self, ball: Ball):
        return isinstance(ball, Heart) # for now

def generate_ball():
    import game
    
    # For testing purpose: 30% chance to get a bomb
    if random.randint(0, 9) < 3:
       return Cutter()
    
    
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