# provides all possible ongoing events. Atm these are:
# - FallingBall. Ball that is lowering over time and soon landing
# - SeesawTilting. One of the four seesaws shifts position because weights have changed recently
# - Scoring. 3 horizontal are expanding, then remove the Balls and score points.

# all must have a .draw(surf) and a .tick(playfield) method.

# shorts:
# - drop_ball(ball, column) to drop a ball from crane-height
# - tilt_seesaw(seesaw, before, after) to move a seesaw from a position to another
# - throw_ball(ball, origin_coords, throwing_range) to throw a ball. Positive throwing_range indicates
# throwing to the right, to higher x-values / columns

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Tuple, List, Type

import game
from balls import Ball, SpecialBall, Bomb, Heart, ColoredBall

from pygame import Surface
from pygame.image import load

from constants import num_columns, max_height, falling_per_tick


# this is a local variable of the module ongoing. Other files, if they import this,
# can use and modify this. Their local name is ongoing.eventQueue
eventQueue: List[Ongoing] = []


def tick() -> None:
    """perform update of all ongoing events. Called periodically as time passes."""
    for event in eventQueue:
        event.tick()


def reset() -> None:
    """empties eventQueue. This sets up the ongoing-module to the state of the game start"""
    global eventQueue
    eventQueue = []


def get_number_of_events() -> int:
    """Returns the number of currently ongoing events"""
    return len(eventQueue)


def get_oldest_event() -> Ongoing:
    """Returns the oldest event that is still ongoing. If there are none, raises IndexError"""
    return eventQueue[0]


def get_newest_event() -> Ongoing:
    """Returns the event that was added last and is still ongoing. If there are none, raises IndexError"""
    return eventQueue[-1]


class Ongoing(ABC):
    """abstract Parent class, should not be instanciated.
    Any child class must have a tick(self, playfield) method and a draw(self,surf) method.
    """

    @abstractmethod
    def tick(self) -> None:
        pass

    @abstractmethod
    def draw(self, surf: Surface) -> None:
        pass


def event_type_exists(eventType: Type[Ongoing]) -> bool:
    """True if at least one such event is currently ongoing"""
    for event in eventQueue:
        if isinstance(event, eventType):
            return True
    return False


def get_event_of_type(eventType: Type[Ongoing]) -> Ongoing:
    """Returns the oldest event of that type that is still ongoing.
    Raises GameStateError if None is there"""
    from game import GameStateError

    for event in eventQueue:
        if isinstance(event, eventType):
            return event
    raise GameStateError(
        f"Requested ongoing Event type {eventType} is not in the eventQueue."
    )


class FallingBall(Ongoing):
    """a Ball that is being dropped, falling after being thrown, or the Ball below it vanished somehow. Vars:

    Constructor: FallingBall(ball, col, starting_height=8.0). The starting height is optional, only to be used
        if the Ball drops from Playfield instead of Crane/Thrown
    """

    ball: Ball
    column: int
    height: float

    def __init__(
        self, ball: Ball, column: int, starting_height: float = float(max_height)
    ):
        self.ball = ball
        self.column = column
        self.height = starting_height

    def draw(self, surf: Surface) -> None:
        from constants import pixel_coord_in_playfield

        x, y = pixel_coord_in_playfield((self.column, self.height))
        self.ball.draw(surf, (x, y))

    def tick(self) -> None:

        self.height -= falling_per_tick
        if self.height >= game.playfield.landing_height_of_column(self.column):
            return

        ball_below = game.playfield.get_top_ball(self.column)
        if isinstance(ball_below, Ball):
            self.ball.lands_on_ball((self.column, int(self.height)), ball_below)
        else:
            self.ball.lands_on_empty((self.column, int(self.height)))
        eventQueue.remove(self)
        game.playfield.refresh_status()

    def getheight(self) -> float:
        return self.height

    def getball(self) -> Ball:
        return self.ball

    def getcolumn(self) -> int:
        return self.column


def drop_ball_in_column(ball: Ball, column: int) -> None:
    eventQueue.append(FallingBall(ball, column))


def ball_falls_from_height(ball: Ball, column: int, height: int) -> None:
    eventQueue.append(FallingBall(ball, column, starting_height=height))


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
        from constants import playfield_ballcoord, playfield_ballspacing

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
        )

        if self.t < 0:
            self.t += thrown_ball_dt
        else:
            self.t += thrown_ball_dt * self.speedup_pastmax

        game.playfield.changed()

        # is the destination reached? If yes, it can become a FallingBall or it can fly out
        if self.t > 1.0:
            if self.destination == -1 or self.destination == num_columns:
                self.fly_out(self.destination == -1)
            else:
                eventQueue.append(
                    FallingBall(
                        self.ball,
                        self.destination,
                        starting_height=thrown_ball_dropheight - 2.0,
                    )
                )
                eventQueue.remove(self)
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
        )

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


def throw_ball(ball: Ball, origin_coords: Tuple[int, int], throwing_range: int) -> None:
    """Throws ball from coords with specified range. Positive range means throwing to the right."""
    eventQueue.append(ThrownBall(ball, origin_coords, throwing_range))


class Scoring(Ongoing):
    """Balls currently scoring points. Expands every few ticks to connected
    Balls of the same color, when finished all the Balls are removed.
    Constructor: Scoring((x,y), ball)
    """

    past: List[Ball]
    next: List[Tuple[int]]
    delay: int
    weight_so_far: int
    ball: Ball  # used in expansion to check if the color matches

    def __init__(self, coords: Tuple[int, int], ball: Ball):
        from constants import scoring_delay

        self.past = []  # list of ScoringColoredBalls
        self.next = [coords]  # list of (int,int) coords in the playfield
        self.delay = scoring_delay
        self.weight_so_far = 0
        self.ball = ball  # this is used to match colors when deciding
        # whether to expand. Should be a ColoredBall or Heart

    def draw(self, surf) -> None:
        # placeholder: Rectangles. Green (65,174,118) for past and slightly
        # brighter green (102,194,164) for next
        pass
        # nextcolor = (102,194,164)
        # for(x,y) in self.next:
        #    xcoord, ycoord = pixel_coord_in_playfield((x,y))
        #    pygame.draw.rect(surf, nextcolor, pygame.Rect((xcoord,ycoord), ball_size), width=3)

    def tick(self) -> None:
        """called once per tick. Counts down delay, expands if zero was reached, and reset delay.
        If no expansion, removes this from the eventQueue
        """

        import game
        from constants import scoring_delay

        self.delay -= 1
        if self.delay > 0:
            return

        if self.expand():
            self.delay = scoring_delay
            return

        if isinstance(self.ball, ColoredBall):
            # Formula for Scores: Total weight x number of balls x level
            score_from_this = (
                self.weight_so_far * len(self.past) * game.level * game.getscorefactor()
            )
            game.addscore(score_from_this)
            # print("Score from this: ", game.addscore(score_from_this))
            # print("Total score: ", game.getscore())
        elif isinstance(self.ball, Heart):
            game.increase_score_factor(len(self.past))
            # print("Global score factor is now ", game.getscorefactor())

        game.playfield.finalize_scoring(self.past)
        game.score_area.changed()
        eventQueue.remove(self)
        game.playfield.refresh_status()

    def expand(self) -> None:
        """checks if neighboring balls are same color, removes them and saves their coords in
        self.next for the next expand() call. Returns True if the Scoring grew.
        """
        from balls import PlayfieldSpace

        now: List[Tuple[int, int]] = self.next
        self.next = []
        for coords in now:
            new_ball: PlayfieldSpace = game.playfield.get_ball_at(coords)
            # do not expand to a position that already has a scoring Ball,
            # and not to a position that does not match colors
            if new_ball.is_scoring() or not new_ball.matches_color(self.ball):
                continue

            new_ball.mark_for_scoring()
            self.weight_so_far += new_ball.getweight()
            self.past.append(new_ball)

            x, y = coords
            coords_to_check: List[Tuple[int, int]] = [
                (x - 1, y),
                (x + 1, y),
                (x, y - 1),
                (x, y + 1),
            ]
            # remove out-of-bounds from this list
            for x2, y2 in coords_to_check:
                if x2 < 0 or x2 > num_columns - 1 or y2 < 0 or y2 > max_height:
                    continue
                self.next.append((x2, y2))

        # print("more matching Balls found: next=",self.next)
        game.playfield.changed()
        return len(self.next) > 0


def start_score(coords) -> None:
    first_ball: Ball = game.playfield.get_ball_at(coords)
    eventQueue.append(Scoring(coords, first_ball))


class Combining(Ongoing):
    """Balls from a vertical Five that combine into one ball with the total weight.
    Once an animation is added to this, this class will make sense. For now, it only serves
    as a placeholder. Counts down for a few ticks, then dies. Drawing is just 'do nothing'.
    Constructor: Combining(coords, color, weight), coords is (int,int)
    """

    coords: Tuple[int, int]
    t: float  # parametrization var, goes from 0.0 to 1.0
    color: int
    weight: int

    def __init__(self, coords: Tuple[int], color: int, weight: int):
        self.coords = coords
        self.color = color
        self.weight = weight
        self.t = 0.0

    def tick(self) -> None:
        from constants import combining_dt

        self.t += combining_dt
        if self.t > 1.0:
            eventQueue.remove(self)
            game.playfield.changed()

    def draw(self, surf: Surface) -> None:
        # draw an ellipse that contracts in y-direction over time
        from colorschemes import simple_standard_ball_colors
        from constants import (
            ball_size,
            rowspacing,
            playfield_ballcoord,
            playfield_ballspacing,
        )
        from pygame.draw import ellipse
        from pygame import Rect

        the_color: Tuple[int, int, int] = simple_standard_ball_colors[self.color]
        starting_ysize: int = 5 * ball_size[1] + 4 * rowspacing
        final_ysize: int = ball_size[1]
        current_ysize: int = starting_ysize + int(
            self.t * (final_ysize - starting_ysize)
        )
        xcoord: int = playfield_ballcoord[0] + self.coords[0] * playfield_ballspacing[0]
        ycoord_final: int = (
            playfield_ballcoord[1]
            + (max_height - 1 - self.coords[1]) * playfield_ballspacing[1]
        )
        ycoord_start: int = (
            playfield_ballcoord[1]
            + (max_height - self.coords[1] - 5) * playfield_ballspacing[1]
        )
        ycoord_now: int = ycoord_start + int(self.t * (ycoord_final - ycoord_start))

        px_coords: Tuple[int, int] = (xcoord, ycoord_now)
        ellipse(surf, the_color, Rect(px_coords, (ball_size[0], current_ysize)))

    def getposition(self) -> Tuple[int, int]:
        """Position of the combining balls, where the resulting ball will be. Returned as a tuple (x,y)"""
        return self.coords


class Explosion(Ongoing):
    """A Bomb has recently exploded here, the sprite is drawn for a few frames."""

    coords: Tuple[int, int]
    progress: float  # from 0.0 to 1.0
    image: Surface

    def __init__(self, coords: Tuple[int, int]):
        x, y = coords
        self.coords = (x - 1, y + 1)
        self.progress = 0.0
        self.image = load("specials/explosion_zugeschnitten.png")

    def tick(self) -> None:
        from constants import explosion_numticks

        self.progress += 1.0 / explosion_numticks
        if self.progress > 1.0:
            eventQueue.remove(self)
            game.playfield.changed()

    def draw(self, surf: Surface) -> None:
        from constants import pixel_coord_in_playfield

        drawpos = pixel_coord_in_playfield(self.coords)
        surf.blit(self.image, drawpos)


def start_explosion(coords) -> None:
    eventQueue.append(Explosion(coords))
