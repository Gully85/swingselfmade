# provides the LandingEffect base class and its subclasses
# A LandingEffect is a consequence of a ball landing. The
# instances are short-lived, this is a hand-over between the
# playfield and the event-handling

from typing import Tuple
from dataclasses import dataclass
from enum import Enum, auto

from balls import Ball


@dataclass
class LandingEffect:
    """A Landing Effect is anything that happens
    as a direct consequence of a ball landing."""

    coords: Tuple[int, int]  # position of the ball that just landed
    landed_ball: Ball


@dataclass
class HorizontalThree(LandingEffect):
    color: int


@dataclass
class VerticalFive(LandingEffect):
    color: int
    totalweight: int


@dataclass
class Explosion(LandingEffect):
    bomb_coords: Tuple[int, int]


@dataclass
class BallIsThrown(LandingEffect):
    ball_to_throw: Ball
    throw_origin_coords: Tuple[int, int]
    throwing_range: int
