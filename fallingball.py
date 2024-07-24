# Class file to hold the FallingBall class

import pygame


from ongoing import Ongoing, remove_from_EQ, add_to_EQ
from constants import max_FPS
from balls import Ball

# speed of falling Balls, in tiles/sec
falling_speed: float = 3.0
# same in tiles/tick
falling_per_tick: float = falling_speed / max_FPS
# Stop if falling Speed is higher than one tile per tick. This would break the FallingBall mechanic
if falling_per_tick > 1.0:
    raise ValueError("Falling Speed too high. Do not fall more than one tile per tick.")


class FallingBall(Ongoing):
    """a Ball that is being dropped, falling after being thrown, or the Ball below it vanished somehow. Vars:

    Constructor: FallingBall(ball, col, starting_height=8.0). The starting height is optional, only to be used
        if the Ball drops from Playfield instead of Crane/Thrown
    """

    from constants import max_height

    ball: Ball
    column: int
    height: float

    def __init__(
        self, ball: Ball, column: int, starting_height: float = float(max_height)
    ):
        self.ball = ball
        self.column = column
        self.height = starting_height

    def draw(self, surf: pygame.Surface) -> None:
        from playfield import Playfield

        x, y = Playfield.pixel_coord_in_playfield((self.column, self.height))
        self.ball.draw(surf, (x, y))

    def tick(self) -> None:

        import game

        self.height -= falling_per_tick
        if self.height >= game.playfield.landing_height_of_column(self.column):
            return

        ball_below = game.playfield.get_top_ball(self.column)
        if isinstance(ball_below, Ball):
            self.ball.lands_on_ball((self.column, int(self.height)), ball_below)
        else:
            self.ball.lands_on_empty((self.column, int(self.height)))
        remove_from_EQ(self)
        game.playfield.refresh_status()

    def getheight(self) -> float:
        return self.height

    def getball(self) -> Ball:
        return self.ball

    def getcolumn(self) -> int:
        return self.column

    @staticmethod
    def drop_ball(ball: Ball, column: int, starting_height=max_height) -> None:
        add_to_EQ(FallingBall(ball, column, starting_height=starting_height))
