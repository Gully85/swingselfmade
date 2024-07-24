# Class file to hold the ThrownBall class


from ongoing import Ongoing, remove_from_EQ, add_to_EQ
from balls import Ball

from typing import Tuple


class ThrownBall(Ongoing):
    """A ball that was thrown by a seesaw. Follows a certain trajectory
    (see comment in tick() for details), then becomes a FallingBall. Vars:
    ball (Colored_Ball or Special_Ball).
    origin (int,int tuple), x and y coordinate of the spot from where it was launched. x=0..7, or
        -1 resp 8 if flying in from the side.
    destination (int), allowed range -1..8. Values 0..7 indicate landing in that column,
        Values -1 or 8 indicate flying out sideway. Destination height is always 8.2

    x (float, not int), allowed range 1.0 <= column <= 8.0. Current position.
    y (float), allowed range 1.0 <= height <= 9.0. Current position.
    remaining_range (int), all values possible. Value is 0 except when it will be thrown out sideway,
        in which case it is the remaining number of columns to be thrown. Not to be confused with the
        constructor argument throwing_range. This is the remaining number of columns after the next fly-out,
        the constructor argument is the total number of columns to fly. Negative if flying to the left
    t (float), running parameter for the trajectory. Values -1 <= t <= +1
    speedup_pastmax (float), factor to the t increase per tick once t>0. Is calculated as (dy_origin)/(dy_destination).


    Constructor: ThrownBall(ball, (x,y), throwing_range), x and y and throwing_range should all be ints.
    Positive throwing_range indicates throwing to the right, negative to the left
    """

    from pygame import Surface

    ball: Ball
    origin: Tuple[int, int]
    destination: int
    x: float
    y: float
    # in case of pending fly-out, this saves the range to fly after the fly-out
    remaining_range: int
    # The trajectory is parametrized with t going from -1.0 to 1.0
    t: float
    # behind the highest point, it speeds up by this factor.
    speedup_pastmax: float

    def __init__(self, ball, coords: Tuple[int], throwing_range: int):
        from constants import thrown_ball_maxheight, thrown_ball_dropheight
        from constants import num_columns

        self.ball = ball
        self.origin = coords
        self.x = float(coords[0])
        self.y = float(coords[1])
        if throwing_range == 0:
            raise ValueError(
                f"Attempting to throw ball {ball} from position {coords} with range zero."
            )

        # calculate destination. Three possible cases: Flying out left, landing in-bound, flying out right.
        destination_raw: int = coords[0] + throwing_range
        if destination_raw < 0:  # fly out left
            self.destination = -1
            self.remaining_range = destination_raw + 1
        elif destination_raw > num_columns:  # fly out right
            self.destination = num_columns
            self.remaining_range = destination_raw - num_columns
        else:  # stay in-bound
            self.destination = destination_raw
            self.remaining_range = 0

        self.t = -1.0

        self.speedup_pastmax = (thrown_ball_maxheight - self.origin[1]) / (
            thrown_ball_maxheight - thrown_ball_dropheight
        )

        print(
            f"Throwing ball {self.ball} from position {self.origin} with range "
            f"{throwing_range}, Destination is {self.destination}, remaining is "
            f"{self.remaining_range}."
        )

        # Maybe generate the trajectory here, as a local lambda(t)?

    @staticmethod
    def throw_ball(
        ball: Ball, origin_coords: Tuple[int, int], throwing_range: int
    ) -> None:
        """Throws ball from coords with specified range. Positive range means throwing to the right."""
        add_to_EQ(ThrownBall(ball, origin_coords, throwing_range))

    def getx(self) -> float:
        """Possible values are 0.0 to 7.0"""
        return self.x

    def gety(self) -> float:
        return self.y

    def getdestination(self) -> int:
        """Returns the destination of this ball-throwing event. Only x-coordinate.
        Possible values are -1 .. 8. -1 for fly-out left, 0..7 for landing, 8 for fly-out right
        """
        return self.destination

    def getball(self) -> Ball:
        """Returns the ball thrown"""
        return self.ball

    def getremaining_range(self) -> int:
        """Returns the remaining throwing range. 0 if landing in-bound, negative if going to fly-out to the left,
        positive if going to fly-out to the right"""
        return self.remaining_range

    def draw(self, surf: Surface) -> None:
        from playfield import playfield_ballcoord, playfield_ballspacing
        from constants import max_height

        # identical to FallingBall.draw() so far
        px_x: int = playfield_ballcoord[0] + self.x * playfield_ballspacing[0]
        px_y: int = (
            playfield_ballcoord[0]
            + int(max_height - 1 - self.y) * playfield_ballspacing[1]
        )
        self.ball.draw(surf, (px_x, px_y))

    def tick(self) -> None:
        # increase t. If destination was reached (t>1), convert into a FallingBall or perform the fly-out.
        # If not, calculate new position x,y from the trajectory.
        from constants import (
            thrown_ball_dt,
            thrown_ball_maxheight,
            thrown_ball_dropheight,
            num_columns,
        )
        from fallingball import FallingBall
        import game

        if self.t < 0:
            self.t += thrown_ball_dt
        else:
            self.t += thrown_ball_dt * self.speedup_pastmax

        game.playfield._changed()

        # is the destination reached? If yes, it can become a FallingBall or it can fly out
        if self.t > 1.0:
            if self.destination == -1 or self.destination == num_columns:
                self.fly_out(self.destination == -1)
            else:
                FallingBall.drop_ball(
                    self.ball,
                    self.destination,
                    starting_height=thrown_ball_dropheight - 2.0,
                )
                remove_from_EQ(self)

            return

        # Ball has not reached its destination yet. Update x and y of the trajectory.
        # The trajectory is a standard parabola -t**2. The t<0 side is for origin to max,
        # t>0 side for max to destination. t=-1 is origin, t=0 is max, t=1 is destination.
        # max is always at x=(origin+destination)/2, y=thrown_ball_maxheight
        # (That implies that the derivative is not smooth at the max. So be it.)
        maxx: int = (self.origin[0] + self.destination) / 2
        maxy: int = thrown_ball_maxheight

        if self.t < 0.0:
            # t<0 origin side: t=0 is (maxx, maxy), t=-1 is origin
            self.x = maxx + self.t * (maxx - self.origin[0])
            self.y = maxy - self.t**2 * (maxy - self.origin[1])
        else:
            # t>0 destination side: Same thing with destination instead of origin
            self.x = maxx - self.t * (maxx - self.destination)
            self.y = maxy - self.t**2 * (maxy - thrown_ball_dropheight)

    def fly_out(self, left: bool) -> None:
        """Ball flew out to the left or right (indicated by argument). Insert it at the
        very right/left, set new origin, calculate and set new destination
        """

        from constants import (
            thrown_ball_flyover_height,
            thrown_ball_maxheight,
            thrown_ball_dropheight,
            num_columns,
        )
        from balls import SpecialBall, Bomb, Heart

        # convert into Heart or Bomb
        if isinstance(self.ball, SpecialBall) and not isinstance(self.ball, Bomb):
            self.ball = Bomb()
        else:
            self.ball = Heart()

        self.t = -1.0
        self.y = thrown_ball_flyover_height
        if left:
            self.x = float(num_columns)
        else:
            self.x = -1.0
        self.origin = (self.x, self.y)

        # calculate new destination. It can be another fly-out (if remaining_range is high enough) or a column.
        # Didn't find a way to make this shorter without losing readability...
        if left:
            if self.remaining_range < -num_columns:
                self.destination = -1
                self.remaining_range += num_columns
            else:  # in-bound
                self.destination = (
                    num_columns - 1 + self.remaining_range
                )  # self.remaining is negative
                self.remaining_range = 0
        else:
            if self.remaining_range > num_columns - 1:
                self.destination = num_columns
                self.remaining_range -= num_columns
            else:
                self.destination = self.remaining_range
                self.remaining_range = 0

        self.speedup_pastmax = (thrown_ball_maxheight - self.origin[1]) / (
            thrown_ball_maxheight - thrown_ball_dropheight
        )
        print(
            f"Ball flying out, left={left}, new remaining_range={self.remaining_range,},"
            f" and destination={self.destination,}"
        )
