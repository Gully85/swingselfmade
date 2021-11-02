# provides the Crane class. The Crane always holds a Ball and has a position (int, 0 to 7).

#from Balls import *
from typing import Tuple
import pygame
from pygame import Rect, Surface
from constants import cranearea_ballcoord, cranearea_x_perCol, ball_size
import balls, depot, ongoing, game

class Crane:
    """Information about the Crane. Has x (int, 0 <= x <= 7) and current_Ball (Ball).
    Also holds a local var surf, surface to draw on, returned when draw() is called on it.
    Constructor expects size of that surface.
    
    Methods:
        drop_ball(), drops ball at the current position, gets a new one from the depot
        move_left()
        move_right(), these two respect boundaries
        getx(), current position 0..7
        getball(), returns the current ball"""
    
    def __init__(self, size: Tuple[int]):
        self.x = 0
        self.current_Ball = balls.generate_starting_ball()
        self.size = size
        self.surf = Surface(size)
        self.changed = True # True if redraw needed. If the Crane changed since the last tick.
    
    def init(self):
        """puts the crane into the state of game start"""
        self.x = 0
        self.current_Ball = balls.generate_starting_ball()
        self.changed = True
        
    def draw(self):
        """draws the Crane and its current_Ball to surface at position, returns surface"""
        self.surf.fill((127,127,127))
        
        xcoord = cranearea_ballcoord[0] + self.x*cranearea_x_perCol
        # draw Ball, then an ellipse on top of it
        self.current_Ball.draw(self.surf, (xcoord, cranearea_ballcoord[1]))
        pixelpos_rect = Rect((xcoord,cranearea_ballcoord[1]), ball_size)
        pygame.draw.ellipse(self.surf, (0,0,0), pixelpos_rect, width=3)
        
        return self.surf
        
    def move_left(self):
        """moves the Crane one position to the left. Does nothing if already in the leftmost position."""
        self.x -= 1
        if self.x < 0:
            self.x = 0
        self.changed = True
        
    
    def move_right(self):
        """moves the Crane one position to the right. Does nothing if already in the rightmost position."""
        self.x += 1
        if self.x > 7:
            self.x = 7
        self.changed = True
    
    def getx(self): 
        """position of the crane. Always returns an int, possible values are 0..7"""
        return self.x

    def getball(self):
        """return the ball currently in the crane. Does not alter the state of the game"""
        return self.current_Ball
    
    def drop_ball(self):
        """drops ball at the current position, gets a new one from the depot"""
        ongoing.ball_falls(self.current_Ball, self.x)
        self.changed = True
        self.current_Ball = game.depot.next_ball(self.x)