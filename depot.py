# provides the Depot. The depot holds 8x2 Balls (array of Balls). This file also provides the drawing method for the Depot.

from typing import Tuple, List
from pygame import Surface

from balls import Ball, generate_starting_ball, generate_ball

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

    size_x: int
    size_y: int
    surf: Surface
    redraw_needed: bool
    content: List[List[Ball]]

    # size in pixels is provided by the constructor call. Initial filling with Colored_Balls is done here for now.
    def __init__(self, size: Tuple[int, int]):
        self.size_x = size[0]
        self.size_y = size[1]
        self.surf = Surface(size)
        self.redraw_needed = True

        self.content = []

        for _ in range(8):
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
        if not self.redraw_needed:
            return

        drawn_depot = self.draw()
        screen.blit(drawn_depot, depot_position)
        self.redraw_needed = False

    def draw(self) -> None:
        """draws full Depot, calls draw() methods of the Balls in the Depot. Returns self.surf"""
        self.surf.fill((127, 127, 127))

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
        the column is not 0..7"""
        if column < 0 or column > 7:
            raise IndexError("Column index must be 0..7")
        ret: Ball = self.content[column][1]
        self.content[column][1] = self.content[column][0]
        self.content[column][0] = generate_ball()
        self.changed()
        return ret
