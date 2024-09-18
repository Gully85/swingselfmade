# contains some code used several times in tests.

import sys

sys.path.append("S:/SwingSelfmade/")


import game, ongoing
from constants import num_columns, tilting_maxticks
from balls import ColoredBall


def wait_for_empty_eq(maxticks: int) -> bool:
    """performs tick()s until nothing is happening any more.
    Parameter is the maximum number of ticks. Return False if
    after that many ticks, something is still going on"""
    for i in range(maxticks - 1):
        game.tick()
        if (
            ongoing.get_number_of_events() == 0
            and not game.playfield.any_seesaw_is_moving()
        ):
            return True

    return False


def make_solid_ground() -> None:
    """Drop two balls of weight 200 (color=1) to the left side of each seesaw,
    then wait for the tilts to finish"""
    for sesa in range(num_columns // 2):
        ball = ColoredBall(1, 200)
        game.playfield.rewritten_land_ball_in_column(ball, sesa * 2)
        ball = ColoredBall(1, 200)
        game.playfield.rewritten_land_ball_in_column(ball, sesa * 2)

    wait_for_empty_eq(tilting_maxticks)
