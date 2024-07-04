# provides the Crane class. The Crane always holds a Ball and has a position (int, 0 to 7).

# from Balls import *
from typing import Tuple
import pygame
from pygame import Rect, Surface
from constants import (
    cranearea_position,
    cranearea_ballcoord,
    cranearea_x_perCol,
    ball_size,
)
from balls import Ball
from balls import generate_starting_ball


class Crane:
    """Information about the Crane. Has x (int, 0 <= x <= 7) and current_Ball (Ball).
    Also holds a local var surf, surface to draw on, returned when draw() is called on it.
    Constructor expects size of that surface.

    Methods:
        drop_ball(), drops ball at the current position, gets a new one from the depot
        move_left()
        move_right(), these two respect boundaries
        move_to_column(int), raises ValueError if out-of-bounds
        getx(), current position 0..7
        getball(), returns the current ball
        drop_ball(), drops current ball"""

    x: int
    current_Ball: Ball
    size: Tuple[int, int]
    surf: Surface
    redraw_needed: bool

    def __init__(self, size: Tuple[int, int]):
        self.x = 0
        self.current_Ball = generate_starting_ball()
        self.size = size
        self.surf = Surface(size)
        self.redraw_needed = True

    def changed(self):
        """trigger a redraw at next opportunity"""
        self.redraw_needed = True

    def reset(self):
        """puts the crane into the state of game start"""
        self.x = 0
        self.current_Ball = generate_starting_ball()
        self.changed()

    def draw_if_changed(self, screen: pygame.Surface):
        if not self.redraw_needed:
            return

        drawn_crane = self.draw()
        screen.blit(drawn_crane, cranearea_position)
        self.redraw_needed = False

    def draw(self):
        """draws the Crane and its current_Ball to surface at position, returns surface"""
        self.surf.fill((127, 127, 127))

        xcoord: int = cranearea_ballcoord[0] + self.x * cranearea_x_perCol
        # draw Ball, then an ellipse on top of it
        self.current_Ball.draw(self.surf, (xcoord, cranearea_ballcoord[1]))
        pixelpos_rect = Rect((xcoord, cranearea_ballcoord[1]), ball_size)
        pygame.draw.ellipse(self.surf, (0, 0, 0), pixelpos_rect, width=3)

        return self.surf

    def move_left(self):
        """moves the Crane one position to the left. Does nothing if already in the leftmost position."""

        if self.x == 0:
            return

        self.x -= 1
        self.changed()

    def move_right(self):
        """moves the Crane one position to the right. Does nothing if already in the rightmost position."""

        if self.x == 7:
            return

        self.x += 1
        self.changed()

    def move_to_column(self, col: int) -> None:
        if col < 0 or col > 7:
            raise ValueError(
                f"Crane column must be 0..7, attempted to move it to column {col}"
            )
        self.x = col
        self.changed()

    def getx(self):
        """position of the crane. Always returns an int, possible values are 0..7"""
        return self.x

    def getball(self):
        """return the ball currently in the crane. Does not alter the state of the game"""
        return self.current_Ball

    def drop_ball(self):
        """drops ball at the current position, gets a new one from the depot"""
        import ongoing, game

        ongoing.drop_ball_in_column(self.current_Ball, self.x)
        self.current_Ball = game.depot.next_ball(self.x)
        self.changed()
