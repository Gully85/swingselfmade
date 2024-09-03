# provides the PendingEffect base class and its subclasses
# A PendingEffect is some event that will soon start a Ongoing
# These are short-lived hand-over instances so the playfield
# can start Ongoings without violating encapsulation

from typing import Tuple
from dataclasses import dataclass

from balls import Ball


@dataclass
class PendingEffect:
    """A Landing Effect is anything that happens
    as a direct consequence of a ball landing."""

    coords: Tuple[int, int]  # position of the ball that just landed
    landed_ball: Ball


@dataclass
class HorizontalThree(PendingEffect):
    color: int


@dataclass
class VerticalFive(PendingEffect):
    color: int
    totalweight: int


@dataclass
class Explosion(PendingEffect):
    bomb_coords: Tuple[int, int]


@dataclass
class BallIsThrown(PendingEffect):
    ball_to_throw: Ball
    throw_origin_coords: Tuple[int, int]
    throwing_range: int


@dataclass
class BallIsDropped(PendingEffect):
    pass
