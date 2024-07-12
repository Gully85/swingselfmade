# provides the Depot. The depot holds 8x2 Balls (array of Balls). This file also provides the drawing method for the Depot.

from typing import Tuple, List
from pygame import Surface

from balls import Ball, generate_starting_ball, generate_ball

from constants import num_columns, column_spacing, window_width, window_height

# Size of area for the depot, relative to screensize
depot_width_fraction, depot_height_fraction = (0.7, 0.2)

# this must be module-scope, since crane-area and playfield need the depot's size
# to calculate their position
depotsize: Tuple[int, int] = (
    int(window_width * depot_width_fraction),
    int(window_height * depot_height_fraction),
)


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

    size_x: int
    size_y: int
    surf: Surface
    redraw_needed: bool
    content: List[List[Ball]]

    # size in pixels is provided by the constructor call. Initial filling with Colored_Balls is done here for now.
    def __init__(self):
        from constants import window_size
        from balls import generate_starting_ball

        window_width, window_height = window_size

        self.size_x = depotsize[0]
        self.size_y = depotsize[1]

        self.surf = Surface(depotsize)
        self.redraw_needed = True

        self.content = []

        for _ in range(num_columns):
            one_row: List[Ball] = []
            one_row.append(generate_starting_ball())
            one_row.append(generate_starting_ball())
            self.content.append(one_row)

    def changed(self) -> None:
        """trigger a redraw"""
        self.redraw_needed = True

    def reset(self) -> None:
        """puts the depot into the state of game start"""
        for i in range(8):
            self.content[i][0] = generate_starting_ball()
            self.content[i][1] = generate_starting_ball()
        self.changed()

    def draw_if_changed(self, screen: Surface) -> None:
        from constants import global_ymargin

        if not self.redraw_needed:
            return

        # Pixel coordinates of the top-left corner of the Depot.
        depot_position_y: int = global_ymargin
        depot_position_x: int = int(0.2 * (1.0 - depot_width_fraction) * window_width)
        depot_position: Tuple[int, int] = (depot_position_x, depot_position_y)

        drawn_depot = self.draw()
        screen.blit(drawn_depot, depot_position)
        self.redraw_needed = False

    def draw(self) -> None:
        """draws full Depot, calls draw() methods of the Balls in the Depot. Returns self.surf"""
        from constants import global_xmargin, global_ymargin, window_width
        from balls import ball_size
        from colorschemes import RGB_lightgrey

        # Calculate Pixel coords of the (top-left corner of the) first Ball in the depot, and
        # distance to second-to-left Ball in the depot.
        # 8 cols of Balls use 8*ballsize[0] px plus 7*colspacing
        px_used: int = 8 * ball_size[0] + 7 * column_spacing
        # Rest of the px is divided equally left and right
        if px_used > self.size_x + 2 * global_xmargin:
            raise ValueError("Depot not wide enough.")

        depot_xleft: int = int(0.5 * (self.size_x - px_used))
        depot_x_perCol: int = ball_size[0] + column_spacing
        # => x-coord of Ball in col i is depot_left + i*depot_x_perCol

        # same for y-direction. Two rows of Balls use (2*ballsize[1] + colspacing) px.
        px_used: int = 2 * ball_size[1] + column_spacing
        if px_used > self.size_y:
            raise ValueError("Depot not high enough.")

        depot_ytop: int = int(0.5 * (self.size_y - px_used))
        depot_y_perRow: int = ball_size[1] + column_spacing

        # it should be sufficient to import these two pairs
        depot_ballcoord: List[int] = [depot_xleft, depot_ytop]
        depot_ballspacing: List[int] = [depot_x_perCol, depot_y_perRow]

        self.surf.fill(RGB_lightgrey)

        for row in range(8):
            px_x: int = depot_ballcoord[0] + row * depot_ballspacing[0]
            px_y: int = depot_ballcoord[1]
            self.content[row][0].draw(
                self.surf,
                (px_x, px_y),
            )
            px_y += depot_ballspacing[1]
            self.content[row][1].draw(
                self.surf,
                (px_x, px_y),
            )

        return self.surf

    def next_ball(self, column: int) -> Ball:
        """get ball of specified column, move ball down and generate a new one. Raise IndexError if
        the column is not 0..num_columns-1"""
        if column < 0 or column > num_columns - 1:
            raise IndexError(f"Column index must be 0..{num_columns}")
        ret: Ball = self.content[column][1]
        self.content[column][1] = self.content[column][0]
        self.content[column][0] = generate_ball()
        self.changed()
        return ret
