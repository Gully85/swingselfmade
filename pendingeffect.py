# provides the PendingEffect base class and its subclasses
# A PendingEffect is some event that will soon start a Ongoing
# These are short-lived hand-over instances so the playfield
# can start Ongoings without violating encapsulation

from typing import Tuple
from dataclasses import dataclass

from balls import Ball


@dataclass
class PendingEffect:
    """A Pending Effect is anything that is supposed to be added to the eventQueue soon"""

    pass


@dataclass
class HorizontalThree(PendingEffect):
    coords: Tuple[int, int]  # position of one of the Balls
    landed_ball: Ball


@dataclass
class VerticalFive(PendingEffect):
    coords: Tuple[int, int]  # position of the lowest Ball
    color: int
    totalweight: int


@dataclass
class Explosion3x3(PendingEffect):
    coords: Tuple[int, int]  # center of the 3x3 area


@dataclass
class BallIsThrown(PendingEffect):
    ball_to_throw: Ball
    throw_origin_coords: Tuple[int, int]
    throwing_range: int  # positive=throw to the right, negative=left


@dataclass
class BallIsDropped(PendingEffect):
    ball: Ball
    column: int
    dropped_from_height: float
