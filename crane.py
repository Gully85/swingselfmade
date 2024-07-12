# provides the Crane class. The Crane always holds a Ball and has a position (int, 0 to 7).

# from Balls import *
from typing import Tuple, List
import pygame
from pygame import Rect, Surface
from constants import num_columns, window_size

from colorschemes import RGB_lightgrey, RGB_black
from balls import Ball, generate_starting_ball
from balls import ball_size

from constants import global_ymargin, column_spacing, window_width, window_height
from depot import depotsize

craneareasize_fraction: Tuple[int, int] = (0.7, 0.1)
craneareasize: Tuple[int, int] = (
    int(window_width * craneareasize_fraction[0]),
    int(window_height * craneareasize_fraction[1]),
)

# this needs to be importable by other modules
# pixel position of the top-left pixel of the crane-area
crane_position_x: int = int(0.2 * (1.0 - craneareasize_fraction[0]) * window_width)
crane_position_y: int = global_ymargin + depotsize[1] + 3
cranearea_position: Tuple[int, int] = (crane_position_x, crane_position_y)


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

    def __init__(self):

        # Size of area where the crane moves, relative to screensize
        window_width, window_height = window_size

        self.x = 0
        self.current_Ball = generate_starting_ball()
        self.size = craneareasize
        self.surf = Surface(self.size)
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

        # Calculate pixel coords of the leftmost position where the Crane can be. And spacing to the second-to-left position etc
        px_used = 8 * ball_size[0] + 7 * column_spacing
        if px_used > self.size[0]:
            raise ValueError("Crane Area not wide enough.")
        cranearea_xleft: int = int(0.5 * (self.size[0] - px_used))
        cranearea_x_perCol: int = ball_size[0] + column_spacing
        # => x-coord of Crane in col i is cranearea_xleft + col*cranearea_x_perCol

        if ball_size[1] > self.size[1]:
            raise ValueError("Crane Area not high enough.")
        cranearea_ytop: int = int(0.5 * (self.size[1] - ball_size[1]))

        cranearea_ballcoord: List[int] = [cranearea_xleft, cranearea_ytop]
        cranearea_ballspacing: List[int] = [0, cranearea_x_perCol]
        self.surf.fill(RGB_lightgrey)

        xcoord: int = cranearea_ballcoord[0] + self.x * cranearea_x_perCol
        # draw Ball, then an ellipse on top of it
        self.current_Ball.draw(self.surf, (xcoord, cranearea_ballcoord[1]))
        pixelpos_rect = Rect((xcoord, cranearea_ballcoord[1]), ball_size)
        pygame.draw.ellipse(self.surf, RGB_black, pixelpos_rect, width=3)

        return self.surf

    def move_left(self):
        """moves the Crane one position to the left. Does nothing if already in the leftmost position."""

        if self.x == 0:
            return

        self.x -= 1
        self.changed()

    def move_right(self):
        """moves the Crane one position to the right. Does nothing if already in the rightmost position."""

        if self.x == num_columns - 1:
            return

        self.x += 1
        self.changed()

    def move_to_column(self, col: int) -> None:
        if col < 0 or col > num_columns - 1:
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
