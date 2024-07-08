# provides the Balls classes

# "Grandparent" class is PlayfieldSpace. This can be an EmptySpace
# or a Ball.
# Ball is an abstract Parent class, can be ColoredBall or SpecialBall
#
# EmptySpace is not abstract, but BlockedSpace inherits from it. BlockedSpace
# is a position blocked by the seesaw state, can only be in the lowest two
# positions of the playfield.

from __future__ import annotations
from typing import Tuple, Type, List
import colorschemes
import pygame
import random
from constants import ball_size, balls_per_level, startlevel
from abc import ABC, abstractmethod
from pygame.font import Font
from pygame import Surface

pygame.font.init()
ball_colors: List[Tuple[int]] = colorschemes.simple_standard_ball_colors
text_colors: List[Tuple[int]] = colorschemes.simple_standard_text_colors
ballfont: Font = pygame.font.SysFont("monospace", 24)

RGB_scoringcolor: Tuple[int, int, int] = (65, 174, 118)

from constants import num_columns, min_balls_between_Specials


class PlayfieldSpace(ABC):
    """Abstract Base Class for a position in the playfield. It can either be a ball
    (whatever kind) or an EmptySpace or BlockedSpace. (BlockedSpace means, blocked by
    seesaw). Must have draw(), getweight() and getcolor() methods."""

    @abstractmethod
    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]) -> None:
        """draw yourself on given surf to given pixel position"""
        pass

    @abstractmethod
    def getweight(self) -> int:
        pass

    @abstractmethod
    def getcolor(self) -> int:
        pass

    @abstractmethod
    def matches_color(self, ball: Ball) -> bool:
        return False

    @abstractmethod
    def is_scoring(self) -> bool:
        return False

    def mark_for_scoring(self) -> None:
        pass


class EmptySpace(PlayfieldSpace):
    """Dummy class for places where there is no Ball. Empty Constructor."""

    def __init__(self):
        pass

    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]) -> None:
        pass

    def getweight(self) -> int:
        return 0

    def getcolor(self) -> int:
        return -1

    def matches_color(self, ball: Ball) -> bool:
        return False

    def is_scoring(self) -> bool:
        return False


class BlockedSpace(PlayfieldSpace):
    """Dummy class for positions blocked by the seesaw state"""

    def __init__(self):
        pass

    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]) -> None:
        # just a black rectangle for now
        pygame.draw.rect(surf, colorschemes.RGB_black, pygame.Rect(drawpos, ball_size))

    def getweight(self) -> int:
        return 0

    def getcolor(self) -> int:
        return -1

    def matches_color(self, ball: Ball) -> bool:
        return False

    def is_scoring(self) -> bool:
        return False


class Ball(PlayfieldSpace):
    """Abstract class indicating that in this space is a ball. Can be either a ColoredBall
    or a SpecialBall."""

    @abstractmethod
    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]) -> None:
        pass

    @abstractmethod
    def getweight(self) -> int:
        return 0

    @abstractmethod
    def getcolor(self) -> int:
        return -1

    @abstractmethod
    def matches_color(self, ball: Ball) -> bool:
        return False

    @abstractmethod
    def is_scoring(self) -> bool:
        """True if the Ball has been marked by an expanding Scoring"""
        return False

    @abstractmethod
    def lands_on_empty(self, coords: Tuple[int, int]) -> None:
        """effects of a Ball landing on an empty side.
        Excluding status update."""
        return None

    @abstractmethod
    def lands_on_ball(self, coords: Tuple[int, int], ball_below: Ball) -> None:
        """effects of a Ball landing on another ball.
        Excluding status update."""
        return None

    def mark_for_scoring(self) -> None:
        pass


class ColoredBall(Ball):
    """Child-class of Ball. Has a color (int, 1 <= color <= maxcolors)
    and a weight (int, 0 or greater). Constructor is Colored_Ball(color, weight)."""

    def __init__(self, color: int, weight: int):
        self.color: int = color
        self.weight: int = weight
        self.scoring: bool = False

    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]) -> None:
        """draws this Ball onto pygame.Surface surf to offset-position drawpos. Returns None"""
        color: Tuple[int] = ball_colors[self.color]

        pixelpos_rect = pygame.Rect(drawpos, ball_size)
        pygame.draw.ellipse(surf, color, pixelpos_rect, 0)
        if self.is_scoring():
            pastcolor: Tuple[int] = RGB_scoringcolor  # for currently scoring balls
            pygame.draw.ellipse(surf, pastcolor, pixelpos_rect, 3)
        weighttext: pygame.Surface = ballfont.render(
            str(self.weight), True, text_colors[self.color]
        )
        posx = drawpos[0] + 0.2 * ball_size[0]
        posy = drawpos[1] + 0.2 * ball_size[1]
        surf.blit(weighttext, (posx, posy))

    def setweight(self, newweight: int) -> None:
        """sets the weight of the ball to given weight"""
        self.weight = newweight

    def getweight(self) -> int:
        """gets weight of the ball"""
        return self.weight

    def setcolor(self, newcolor: int) -> None:
        self.color = newcolor

    def getcolor(self) -> int:
        return self.color

    def matches_color(self, ball: Ball) -> bool:
        # TODO Joker
        if not isinstance(ball, ColoredBall):
            return False
        return ball.getcolor() == self.color

    def mark_for_scoring(self) -> None:
        """Converts Ball to ScoringColoredBall, returns new one"""
        self.scoring = True

    def is_scoring(self) -> bool:
        return self.scoring

    def lands_on_empty(self, coords: Tuple[int, int]) -> None:
        import game

        game.playfield.add_on_top(self, coords[0])

    def lands_on_ball(self, coords: Tuple[int, int], ball_below: Ball) -> None:
        import game

        game.playfield.add_on_top(self, coords[0])


class SpecialBall(Ball):
    """abstract class. Must be instanciated as one of the SpecialBall types. These all have weight==0.
    Must implement draw(surf, drawpos) and land_on_bottom(coords) and land_on_ball(coords).
    """

    image: pygame.Surface
    level_required: int

    @abstractmethod
    def __init__(self):
        pass

    def getweight(self) -> int:
        return 0

    def getcolor(self) -> int:
        return -1

    @abstractmethod
    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]) -> None:
        surf.blit(self.image, drawpos)
        # somehow make sure that self.image exists. @property decorator?

    @abstractmethod
    def landing_effect_on_ground(self, coords: Tuple[int]) -> None:
        pass

    @abstractmethod
    def landing_effect_on_ball(self, coords: Tuple[int]) -> None:
        pass

    @abstractmethod
    def matches_color(self, ball: Ball) -> bool:
        return False

    def is_scoring(self) -> bool:
        """Most SpecialBalls can not score, so False is the default answer.
        This is overriden in the exceptions: Heart and Star"""
        return False

    @abstractmethod
    def lands_on_empty(self, coords: Tuple[int, int]) -> None:
        return None

    @abstractmethod
    def lands_on_ball(self, coords: Tuple[int, int], ball_below: Ball) -> None:
        return None


class Bomb(SpecialBall):
    """Special Ball. If landing on a Ball, it explodes a 3x3 area. If landing on a BlockedSpace, it
    just lies around, but explodes once any Ball lands on it or a neighboring Bomb explodes.
    """

    level_required: int = 4
    image: Surface = pygame.image.load("specials/bombe-selbstgemalt.png")

    def __init__(self):
        pass

    def draw(self, surf: pygame.Surface, drawpos: Tuple[int, int]) -> None:
        super().draw(surf, drawpos)

    def landing_effect_on_ground(self, coords: Tuple[int, int]) -> None:
        pass

    def landing_effect_on_ball(self, coords: Tuple[int, int]) -> None:
        self.explode(coords)

    def explode(self, coords: Tuple[int, int]) -> None:
        import game
        from playfield import Playfield

        the_playfield: Playfield = game.playfield
        # TODO in 3x3 area: Display explosion sprite (ongoing), explode bombs, remove other balls
        xcenter, ycenter = coords
        xcenter = int(xcenter)
        ycenter = int(ycenter)

        game.ongoing.start_explosion(coords)
        the_playfield.remove_ball_at(coords)

        for x in range(xcenter - 1, xcenter + 2):
            if x < 0 or xcenter > num_columns - 1:
                continue
            for y in range(ycenter - 1, ycenter + 2):
                if y < 0 or y > num_columns - 1:
                    continue
                ball_there = the_playfield.get_ball_at((x, y))
                if isinstance(ball_there, Bomb):
                    ball_there.explode((x, y))
                elif isinstance(ball_there, Ball):
                    the_playfield.remove_ball_at((x, y))

        the_playfield.refresh_status()

    def matches_color(self, ball: Ball) -> bool:
        return False

    def lands_on_empty(self, coords: Tuple[int, int]) -> None:
        import game

        game.playfield.add_on_top(self, coords[0])

    def lands_on_ball(self, coords: Tuple[int, int], ball_below: Ball) -> None:
        import game

        game.playfield.trigger_explosion(coords)


class Cutter(SpecialBall):
    """Special Ball. Destroys the stack it lands on. Once hitting the BlockedSpace or
    height 0, it disappears."""

    level_required: int = 5
    image: Surface = pygame.image.load("specials/bohrer-selbstgemalt.png")

    def __init__(self):
        pass

    def draw(self, surf: pygame.Surface, drawpos: Tuple[int, int]) -> None:
        super().draw(surf, drawpos)

    def landing_effect_on_ground(self, coords: Tuple[int, int]):
        import game

        game.playfield.remove_ball_at(coords)

    def landing_effect_on_ball(self, coords: Tuple[int]) -> None:
        import game

        x, y = coords
        game.playfield.remove_ball_at((x, y - 1))
        game.playfield.remove_ball_at(coords)
        game.ongoing.ball_falls_from_height(self, x, y)

    def matches_color(self, ball: Ball) -> bool:
        return False

    def lands_on_empty(self, coords: Tuple[int, int]) -> None:
        pass

    def lands_on_ball(self, coords: Tuple[int, int], ball_below: Ball) -> None:
        import game

        game.playfield.remove_ball_at((coords[0], coords[1] - 1))
        game.ongoing.ball_falls_from_height(self, coords[0], coords[1])


class Heart(SpecialBall):
    """No special effects. When Scoring, this will increase the global
    score factor by 0.1*(number of Hearts scored)"""

    level_required: int = 4
    image: Surface = pygame.image.load("specials/Herz-selbstgemalt.png")

    def __init__(self):
        self.scoring = False

    def draw(self, surf: pygame.Surface, drawpos: Tuple[int]) -> None:
        super().draw(surf, drawpos)

    def landing_effect_on_ground(self, coords: Tuple[int]) -> None:
        pass

    def landing_effect_on_ball(self, coords: Tuple[int]) -> None:
        pass

    def matches_color(self, ball: Ball) -> bool:
        return isinstance(ball, Heart)  # for now. TODO Joker

    def mark_for_scoring(self) -> None:
        self.scoring = True

    def is_scoring(self) -> bool:
        return self.scoring

    def lands_on_ball(self, coords: Tuple[int, int], ball_below: Ball) -> None:
        import game

        return game.playfield.add_on_top(self, coords[0])

    def lands_on_empty(self, coords: Tuple[int, int]) -> None:
        import game

        return game.playfield.add_on_top(self, coords[0])


nextspecial = Bomb()
nextspecial_delay = 5


def regenerate_nextspecial() -> None:
    """Resets the upcoming special and timer
    to new randomly generated ones"""
    import game

    random_pool: Type[SpecialBall] = [Bomb, Cutter, Heart]
    pick: Type[SpecialBall] = random.choice(random_pool)
    while pick.level_required > game.level:
        pick = random.choice(random_pool)

    global nextspecial, nextspecial_delay
    nextspecial = pick()
    nextspecial_delay = random.randint(
        int(0.8 * pick.level_required), int(1.2 * pick.level_required)
    )
    if nextspecial_delay < min_balls_between_Specials:
        nextspecial_delay = min_balls_between_Specials
    # print("next upcoming Special: " + pick + " in " + nextspecial_delay)


def getnextspecial() -> SpecialBall:
    return nextspecial


def getnextspecial_delay() -> int:
    """Number of moves until the next SpecialBall reaches the Depot"""
    return nextspecial_delay


def generate_ball() -> Ball:
    import game

    # TODO Star at levelup

    global nextspecial_delay
    if nextspecial_delay == 0:
        ret = nextspecial
        regenerate_nextspecial()
        return ret

    nextspecial_delay -= 1

    # in the first 20% of each level, the new color is more likely
    if game.balls_dropped % balls_per_level < int(
        0.2 * balls_per_level
    ) and random.choice([True, False]):
        color = game.level - 1
    else:
        color = random.randint(1, game.level - 1)
    weight = random.randint(1, game.level)
    return ColoredBall(color, weight)


def generate_starting_ball():
    """This will always generate a ColoredBall."""
    color = random.randint(0, startlevel - 1)
    weight = random.randint(1, startlevel)
    return ColoredBall(color, weight)


def force_special(char: str):
    """Forces the next generated ball to be a Bomb/Cutter/Heart,
    depending on char being B/C/H. If not B/C/H, do nothing"""
    return
    global nextspecial, nextspecial_delay
    if char == "B":
        nextspecial = Bomb()
    elif char == "C":
        nextspecial = Cutter()
    elif char == "H":
        nextspecial = Heart()
    else:
        return
    nextspecial_delay = 1
