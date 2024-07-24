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
import pygame

import game
from constants import max_FPS
from balls import Ball


# this is a local variable of the module ongoing. Other files, if they import this,
# can use and modify this. Their local name is ongoing.eventQueue
eventQueue: List[Ongoing] = []


def remove_from_EQ(event: Ongoing) -> None:
    """Remove given event from Event-Queue. Raise Error if it isn't in the EQ."""
    global eventQueue
    eventQueue.remove(event)


def add_to_EQ(event: Ongoing) -> None:
    global eventQueue
    eventQueue.append(event)


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
    def draw(self, surf: pygame.Surface) -> None:
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
        from balls import ColoredBall, Heart

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
        elif isinstance(self.ball, Heart):
            game.increase_score_factor(len(self.past))

        game.playfield.finalize_scoring(self.past)
        eventQueue.remove(self)
        game.playfield.refresh_status()

    def expand(self) -> None:
        """checks if neighboring balls are same color, removes them and saves their coords in
        self.next for the next expand() call. Returns True if the Scoring grew.
        """
        from balls import PlayfieldSpace
        from constants import num_columns, max_height

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

    def draw(self, surf: pygame.Surface) -> None:
        # draw an ellipse that contracts in y-direction over time
        from colorschemes import simple_standard_ball_colors
        from constants import row_spacing
        from balls import ball_size
        from playfield import playfield_ballspacing, playfield_ballcoord, max_height
        from pygame.draw import ellipse
        from pygame import Rect

        the_color: Tuple[int, int, int] = simple_standard_ball_colors[self.color]
        starting_ysize: int = 5 * ball_size[1] + 4 * row_spacing
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
    image: pygame.Surface

    def __init__(self, coords: Tuple[int, int]):
        x, y = coords
        self.coords = (x - 1, y + 1)
        self.progress = 0.0
        self.image = pygame.image.load("specials/explosion_zugeschnitten.png")

    def tick(self) -> None:
        from constants import explosion_numticks

        self.progress += 1.0 / explosion_numticks
        if self.progress > 1.0:
            eventQueue.remove(self)
            game.playfield.changed()

    def draw(self, surf: pygame.Surface) -> None:
        from playfield import Playfield

        drawpos = Playfield.pixel_coord_in_playfield(self.coords)
        surf.blit(self.image, drawpos)


def start_explosion(coords) -> None:
    eventQueue.append(Explosion(coords))
