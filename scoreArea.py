# Scoring area, where the current level, number of dropped balls and Score is shown

from typing import Tuple
import pygame

from constants import startlevel, window_size, global_xmargin
from playfield import playfield_position, playfieldsize
from balls import ColoredBall

ballsdropped_font = pygame.font.SysFont("Arial", 16)
score_font = pygame.font.SysFont("Arial", 16)


# area where the score-display is. Located 5px to the right of the playfield-area
px_used = playfield_position[0] + playfieldsize[0]

scoredisplayarea_position_x: int = px_used + 5
scoredisplayarea_position_y: int = playfield_position[1]
scoredisplayarea_position: Tuple[int, int] = (
    scoredisplayarea_position_x,
    scoredisplayarea_position_y,
)

scoredisplayarea_size_x: int = window_size[0] - px_used - global_xmargin
scoredisplayarea_size_y: int = playfieldsize[1]
scoredisplayarea_size: Tuple[int, int] = (
    scoredisplayarea_size_x,
    scoredisplayarea_size_y,
)


class ScoreArea:
    """Information about the score display area. Stores a local pygame.Surface.
    Stores a Colored_Ball to show the current level

    Vars:
        surf (pygame.Surface)
        size (int,int)
        changed (bool), True if redraw is needed
        levelball (Colored_Ball), whose draw() method is called on each redraw.
    Constructor: ScoreArea((size_x, size_y))
    Methods
    """

    surf: pygame.Surface
    size: Tuple[int, int]
    redraw_needed: bool
    levelball: ColoredBall

    def __init__(self):

        self.size = scoredisplayarea_size
        self.surf = pygame.Surface(self.size)
        self.redraw_needed = True
        self.levelball = ColoredBall(startlevel, startlevel)

    def _changed(self) -> None:
        self.redraw_needed = True

    def draw_if_changed(self, screen: pygame.Surface) -> None:
        if not self.redraw_needed:
            return
        else:
            drawn_scorearea = self.draw()
            screen.blit(drawn_scorearea, scoredisplayarea_position)

    def draw(self) -> None:
        from game import balls_dropped, score
        from colorschemes import RGB_lightgrey, RGB_black
        from balls import ball_size, getnextspecial_delay, getnextspecial

        self.surf.fill(RGB_lightgrey)

        # Level is at the top, as a Colored_Ball of the newest Color, with the level as weight

        # x position is a centered Colored_ball
        px_used: int = ball_size[0]
        level_position_x: int = 0.5 * (self.size[0] - px_used)
        level_position_y: int = 0.1 * self.size[1]
        level_position: Tuple[int, int] = (level_position_x, level_position_y)

        self.levelball.draw(self.surf, level_position)

        ballsdropped_text: pygame.Surface = ballsdropped_font.render(
            "Balls dropped: " + str(balls_dropped), True, RGB_black
        )
        ballsdropped_position_x: int = int(0.1 * self.size[0])
        ballsdropped_position_y: int = int(0.4 * self.size[1])
        ballsdropped_position: Tuple[int, int] = (
            ballsdropped_position_x,
            ballsdropped_position_y,
        )
        self.surf.blit(ballsdropped_text, ballsdropped_position)

        score_text: pygame.Surface = score_font.render(
            "Score: " + str(score), True, RGB_black
        )
        score_position_x: int = ballsdropped_position_x
        score_position_y: int = 0.8 * self.size[1]
        score_position: Tuple[int, int] = (score_position_x, score_position_y)
        self.surf.blit(score_text, score_position)

        nextspecial_text: pygame.Surface = score_font.render(
            "Next Special in " + str(getnextspecial_delay()), True, RGB_black
        )
        nextspecial_position_x: int = score_position_x
        nextspecial_position_y: int = int(0.6 * self.size[1])
        nextspecial_position: Tuple[int, int] = (
            nextspecial_position_x,
            nextspecial_position_y,
        )
        nextspecial_ballpos: Tuple[int, int] = (
            nextspecial_position_x + 125,
            nextspecial_position_y,
        )
        self.surf.blit(nextspecial_text, nextspecial_position)
        getnextspecial().draw(self.surf, nextspecial_ballpos)

        return self.surf

    def update_level(self):
        from game import level

        self.levelball = ColoredBall(level, level)
