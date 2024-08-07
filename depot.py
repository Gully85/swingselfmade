# provides the Depot. The depot holds 8x2 Balls (array of Balls). This file also provides the drawing method for the Depot.

from typing import Tuple

import balls
#from pygame import Surface 
import pygame
from constants import depot_position, depot_ballcoord, depot_ballspacing

class Depot:
    """Information about the Depot state. Balls stored here, and drawing procedure. 
    Vars:
        size (tuple int, int), drawing size in pixels
        changed (bool), True if redraw is needed
        surf (pygame.Surface), draw() will draw everything on this and return it
    Constructor: Depot((size_x, size_y))	
    Methods:
        next_ball(int), get ball of specified column, move ball down and generate a new one
    """
    
    # size in pixels is provided by the constructor call. Initial filling with Colored_Balls is done here for now. 
    def __init__(self, size: Tuple[int]):
        self.size_x = size[0]
        self.size_y = size[1]
        self.surf = pygame.Surface(size)
        self.redraw_needed = True

        # init empty to set array size to 8x2
        self.content = [[None,None], [None,None], [None,None], [None,None],
                        [None,None], [None,None], [None,None], [None,None]]
        # second index is bot or top-row. 0 is top row (spawned Balls appear here), 
        # 1 is bot row (Crane takes from here, moving top-row here and spawning a new Ball in top-row)

        # fill with randomly generated Balls
        for i in range(8):
            self.content[i][0] = balls.generate_starting_ball()
            self.content[i][1] = balls.generate_starting_ball()
    
    def changed(self):
        """trigger a redraw"""
        self.redraw_needed = True
    
    def reset(self):
        """puts the depot into the state of game start"""
        for i in range(8):
            self.content[i][0] = balls.generate_starting_ball()
            self.content[i][1] = balls.generate_starting_ball()
        self.changed()
    
    def draw_if_changed(self, screen: pygame.Surface):
        if not self.redraw_needed:
            return
        else:
            drawn_depot = self.draw()
            screen.blit(drawn_depot, depot_position)
            self.redraw_needed = False

    def draw(self):
        """draws full Depot, calls draw() methods of the Balls in the Depot. Returns self.surf"""
        self.surf.fill((127,127,127))
        
        for row in range(8):
            self.content[row][0].draw(self.surf, (depot_ballcoord[0] + row*depot_ballspacing[0], depot_ballcoord[1]))
            self.content[row][1].draw(self.surf, (depot_ballcoord[0] + row*depot_ballspacing[0], depot_ballcoord[1]+depot_ballspacing[1]))
        
        return self.surf
    
    def next_ball(self, column: int):
        """get ball of specified column, move ball down and generate a new one. Raise IndexError if 
        the column is not 0..7"""
        if column < 0 or column > 7:
            raise IndexError("Column index must be 0..7")
        ret = self.content[column][1]
        self.content[column][1] = self.content[column][0]
        self.content[column][0] = balls.generate_ball()
        self.changed()
        return ret