# provides the Playfield class. The playfield has 8 stacks of Balls
# (lowest 0-2 are blocked, depending on seesaw state). An empty space in the playfield
# is represented as None, same for a blocked space at the bottom.

from __future__ import annotations

debugprints = False

from typing import Tuple, List


from pygame import Surface, Rect
from pygame.transform import threshold
from pygame.draw import rect as draw_rect
import balls, game
from balls import PlayfieldSpace, Ball

from colorschemes import RGB_lightgrey

import ongoing

# from constants import playfield_ballcoord, playfield_ballspacing
from constants import pixel_coord_in_playfield
from constants import playfield_position, ball_size

from constants import num_columns, max_height, tilting_per_tick

from pygame.font import SysFont

weightdisplayfont = SysFont("Arial", 12)


class Playfield:
    """Information about the current Playfield.
    Constructor takes size in pixels as (width,height) tuple."""

    def __init__(self, size: Tuple[int, int]):
        numstacks = num_columns // 2
        self.stacks: List[Seesaw] = []

        for i in range(numstacks):
            self.stacks.append(Seesaw(2 * i))

        self.size: Tuple[int, int] = size
        self.surf: Surface = Surface(size)
        self.redraw_needed: bool = True
        self.alive: bool = True

    def tick(self) -> None:
        for sesa in self.stacks:
            sesa.tick()

    def reset(self) -> None:
        self.__init__(self.size)

    def changed(self) -> None:
        """trigger a redraw at next opportunity"""
        self.redraw_needed = True

    def draw_if_changed(self, screen: Surface) -> None:
        """draws Playfield if it changed or if any event is ongoing"""

        trigger_redraw: bool = self.redraw_needed
        trigger_redraw |= game.ongoing.get_number_of_events() > 0

        if not trigger_redraw:
            return

        drawn_playfield: Surface = self.draw()
        for event in game.ongoing.eventQueue:
            event.draw(drawn_playfield)
        screen.blit(drawn_playfield, playfield_position)
        self.redraw_needed = False

    def draw(self) -> Surface:
        """draws the Playfield including all Balls."""
        self.surf.fill(RGB_lightgrey)

        for x in range(num_columns // 2):
            self.stacks[x].draw(self.surf)

        return self.surf

    def get_ball_at(self, coords: Tuple[int, int]) -> PlayfieldSpace:
        """Returns ball at position, or EmptySpace/Blocked if there is no ball at that position. Coords must
        be (x,y) with x=0..7 and y=0..7
        Blocked is returned if that position is blocked by the seesaw state, only possible for y=0 or y=1
        """
        x, y = coords
        if x < 0 or x > num_columns - 1 or y < 0 or y > num_columns - 1:
            raise IndexError("can't get Ball from position ({},{})".format(x, y))

        return self.stacks[x // 2].get_ball_at_height(y, x % 2 == 0)

    def column_is_empty(self, column: int) -> bool:
        if column < 0 or column > num_columns - 1:
            raise ValueError(
                f"Trying to get empty-status of column {column}, "
                f"only 0..{num_columns - 1} possible"
            )
        sesa: int = column // 2
        return self.stacks[sesa].isempty(column % 2 == 0)

    def add_on_top(self, ball: Ball, column: int) -> None:
        """add a Ball on top of a stack, do not trigger anything"""
        if column < 0 or column > num_columns:
            raise ValueError("Wrong column {}".format(column))
        self.stacks[column // 2].add_on_top(ball, column % 2 == 0)

    def get_weight_of_column(self, column: int) -> int:
        """Returns total weight of the stack in given column 0..7."""
        if column < 0 or column > num_columns - 1:
            raise ValueError(
                f"Trying to get weight of column {column}, "
                f"only 0..{num_columns} possible"
            )

        x: int = column // 2  # 0..3 possible
        sesa: Seesaw = self.stacks[x]
        sesa.update_weight()
        return sesa.getweight(x % 2 == 0)

    def check_alive(self) -> bool:
        """False if any stack is too high. Max 6-8 balls per stack are allowed,
        depending on seesaw tilt position. Moving seesaws never trigger a loss"""
        for sesa in self.stacks:
            if not sesa.check_alive():
                return False
        return True

    def land_ball_in_column(self, ball: Ball, x: int) -> None:
        """Land a ball in specified column on top of the stack. x=0..7.
        Does not trigger on-land effects."""
        self.stacks[x // 2].add_on_top(ball, x % 2 == 0)
        self.refresh_status()

    def trigger_explosion(self, coords: Tuple[int, int]) -> None:
        """Trigger an explosion centered at given position."""
        ongoing.start_explosion(coords)
        x, y = coords

        self.remove_ball_at((x, y))
        # area of the explosion, respect boundaries
        coords_to_blowup: List[Tuple[int, int]] = []
        for x2 in range(x - 1, x + 2):
            if x2 < 0 or x2 > num_columns - 1:
                continue
            for y2 in range(y + 1, y - 2, -1):
                if y2 < 0 or y2 > num_columns:
                    continue
                coords_to_blowup.append((x2, y2))

        for position in coords_to_blowup:
            ball_there = self.get_ball_at(position)
            if isinstance(ball_there, balls.Bomb):
                self.trigger_explosion(position)
            self.remove_ball_at(position)

    def refresh_status(self) -> None:
        """Checks if anything needs to start now. Performs weight-check,
        if that does nothing performs scoring-check, if that does nothing performs combining-check.
        """

        if not self.gravity_moves():
            if not self.check_Scoring_full():
                self.check_combining()

        if not self.check_alive():
            self.alive = False

    def update_weights(self) -> None:
        """updates all weights"""
        for sesa in self.stacks:
            sesa.update_weight()

    def gravity_moves(self) -> bool:
        """calculates all weights, compares with seesaw state, pushes if necessary, throws if necessary.
        Returns True if any seesaw moved. Adds SeesawTilting and ThrownBall to the eventQueue if necessary.
        """
        ret = False
        for sesa in self.stacks:
            sesa.update_weight()
            if sesa.check_gravity():
                sesa.throw_top_ball()
            if sesa.ismoving():
                ret = True

        return ret

    def any_seesaw_is_moving(self) -> bool:
        """True if at least one of the seesaws is moving."""
        for stack in self.stacks:
            if stack.ismoving():
                return True
        return False

    def check_Scoring_full(self) -> bool:
        """checks the full content for any horizontal-threes of the same color.
        Adds a Scoring to the eventQueue if one was found.
        Returns True if a Scoring was found.
        Checks bottom-up, only the lowest row with a horizontal-three is checked, only the leftmost Three is found.
        """

        # lowest row can never Score. Start at height 1
        for y in range(1, num_columns):
            # x=1..6 makes sure that (x +/- 1) stays in-bound 0..7
            for x in range(1, num_columns - 1):
                the_ball = self.get_ball_at((x, y))
                if not isinstance(the_ball, balls.Ball):
                    continue

                # TODO Joker, Heart, Star

                left_neighbor: PlayfieldSpace = self.get_ball_at((x - 1, y))
                if not left_neighbor.matches_color(the_ball):
                    continue
                right_neighbor: PlayfieldSpace = self.get_ball_at((x + 1, y))
                if right_neighbor.matches_color(the_ball):
                    ongoing.start_score((x, y))
                    return True
        return False

    def check_combining(self) -> bool:
        """Checks the full gameboard for vertical Fives. Only one per stack is possible.
        Combines if one is found, and creates an Ongoing.Combining. Returns True if any are found
        """
        return False
        # obsolete code below
        # print("Entering full Combining check")
        for x in range(8):
            for y in range(0, 4):
                this_color = self.content[x][y].getcolor()
                if this_color == -1:
                    continue
                # if this point is reached, the current ball is a Colored_Ball. All others have the
                # attribute color==-1
                total_weight = self.content[x][y].getweight()

                # five balls are needed: y, y+1, ..., y+4. If this loop reaches y+5, do not check
                # the (y+5)-position, but Combine instead
                for check_height in range(y + 1, y + 6):
                    if check_height == y + 5:
                        ret = True
                        self.content[x][y] = ColoredBall(this_color, total_weight)
                        ongoing.eventQueue.append(
                            ongoing.Combining((x, y), this_color, total_weight)
                        )
                        self.content[x][y + 1] = EmptySpace()
                        self.content[x][y + 2] = EmptySpace()
                        self.content[x][y + 3] = EmptySpace()
                        self.content[x][y + 4] = EmptySpace()
                        break

                    if self.content[x][check_height].getcolor() != this_color:
                        break

                    total_weight += self.content[x][check_height].getweight()

        if ret:
            self.check_hanging_balls()
            self.changed()

        return ret

    def finalize_scoring(self, balls: list) -> None:
        """Remove all the (marked) balls supplied"""
        for sesa in self.stacks:
            sesa.remove_scored_balls(balls)

    def get_number_of_balls(self) -> int:
        """Returns the number of balls currently lying in the playfield. Not counting FallingBalls
        or ThrownBalls."""
        ret = 0
        for sesa in self.stacks:
            ret += sesa.get_number_of_balls()

        return ret

    def get_seesaw_state(self, column: int) -> int:
        """Returns current tilt status of column (0..7) as int. -1, 0 or +1 for
        low, balanced, high. If moving, rounded towards nearest position."""
        sesa = self.stacks[column // 2]
        raw_tilt = sesa.gettilt()
        left = column % 2 == 0
        # tilt is -1 for heavier left and +1 for heavier right. Right is negative raw_tilt
        if left:
            return round(raw_tilt)
        else:
            return round(-raw_tilt)

    def remove_ball_at(self, coords: Tuple[int, int]) -> None:
        """remove a ball from specified position. If there is already no ball, do nothing. If the position
        is Blocked, raises GameStateError"""
        x, y = coords
        if x < 0 or x > num_columns - 1 or y < 0:
            raise ValueError(
                f"Trying to remove ball from position {coords}, that is out of bounds"
            )

        sesa: Seesaw = self.stacks[x // 2]
        sesa.remove_ball_at(coords)

    def landing_height_of_column(self, column: int) -> int:
        """Returns the height of the lowest EmptySpace position of a column. Possible values are 1..8"""
        sesa = self.stacks[column // 2]
        return sesa.landing_height(column % 2 == 0)

    def get_top_ball(self, column: int) -> PlayfieldSpace:
        """returns highest ball in the stack, or BlockedSpace if the stack is empty"""
        if column < 0 or column > num_columns:
            raise ValueError(
                "Can not get top of ball of stack {},"
                "only 0..7 possible".format(column)
            )
        if self.column_is_empty(column):
            return balls.BlockedSpace()
        else:
            return self.stacks[column // 2].get_top_ball(column % 2 == 0)


class Seesaw:
    """A pair of two connected stacks in the playfield."""

    def __init__(self, xleft):
        self.tilt: float = 0.0  # 0 for balanced, #-1 for heavier left
        # side, +1 for heavier right side
        self.weightleft: int = 0
        self.weightright: int = 0
        self.stackleft: List[Ball] = []  # first is lowest, last is highest Ball
        self.stackright: List[Ball] = []  # first is lowest, last is highest Ball
        self.moving: bool = False
        self.xleft: int = xleft  # should always be an even number

    def ismoving(self) -> bool:
        return self.moving

    def isempty(self, left: bool) -> bool:
        if left:
            return len(self.stackleft) == 0
        else:
            return len(self.stackright) == 0

    def landing_height(self, left: bool) -> int:
        blockedheight: float = self.get_blocked_height(left)
        if left:
            return blockedheight + len(self.stackleft)
        else:
            return blockedheight + len(self.stackright)

    def explode_bombs(self, left: bool) -> None:
        """If the stack is not moving and contains bombs,
        trigger their explosion"""
        if self.ismoving():
            return

        if left:
            stack = self.stackleft
        else:
            stack = self.stackright
        blockedheight = self.get_blocked_height(left)
        for y, ball in enumerate(stack):
            if isinstance(ball, balls.Bomb):
                ball.explode((self.xleft + (1 - left), y + blockedheight))

    def check_gravity(self) -> bool:
        """Sets state to moving if weights dont fit
        with the current tilt. Returns True if this
        started the seesaw to move."""
        if self.ismoving():
            return False

        if self.weightleft > self.weightright:
            target_tilt = -1.0
        elif self.weightleft == self.weightright:
            target_tilt = 0.0
        else:
            target_tilt = 1.0

        if target_tilt != self.tilt:
            self.moving = True

        return self.moving

    def getweight(self, left: bool) -> int:
        """Weight of one stack."""
        if left:
            return self.weightleft
        else:
            return self.weightright

    def gettilt(self) -> float:
        """-1 for heavier left, 0 for balanced,
        +1 for heavier right. Can have any float value
        between -1.0 and +1.0."""
        return self.tilt

    def add_on_top(self, ball: balls.Ball, left: bool) -> None:
        if left:
            self.stackleft.append(ball)
        else:
            self.stackright.append(ball)

    def get_top_ball(self, left: bool) -> Ball:
        if left:
            return self.stackleft[-1]
        else:
            return self.stackright[-1]

    # TODO can this be removed?
    def get_ball_at_height(self, height: int, left: bool) -> PlayfieldSpace:
        # TODO what if moving? Both? Return Dummy object?
        if left:
            stack = self.stackleft
        else:
            stack = self.stackright
        blockedheight = round(self.get_blocked_height(left))
        height = round(height)
        if height < blockedheight:
            return balls.BlockedSpace()
        elif height >= blockedheight + len(stack):
            return balls.EmptySpace()
        else:
            return stack[height - blockedheight]

    def get_blocked_height(self, left: bool) -> float:
        """Returns the number of blocked space at the bottom as float.
        Must be round()'ed to get integer 0,1,2"""
        if left:
            return 1.0 + self.tilt
        else:
            return 1.0 - self.tilt

    def update_weight(self) -> int:
        """calculates total weight of both sides,
        updates internal weight variable"""
        self.weightleft = 0
        for ball in self.stackleft:
            self.weightleft += ball.getweight()
        self.weightright = 0
        for ball in self.stackright:
            self.weightright += ball.getweight()

    def tick(self) -> None:
        """if moving, tilt further. Check if tilting is done."""
        if not self.moving:
            return

        game.playfield.changed()
        # if left is heavier, reduce tilt
        if self.weightleft > self.weightright:
            self.tilt -= tilting_per_tick
            if self.tilt <= -1.0:
                self.tilt = -1.0
                self.finalize_tilting()
        # if weights are equal, move tilt towards zero
        elif self.weightleft == self.weightright:
            if self.tilt > 0.0:
                self.tilt -= tilting_per_tick
                if self.tilt <= 0.0:
                    self.tilt = 0.0
                    self.finalize_tilting()
            else:
                self.tilt += tilting_per_tick
                if self.tilt >= 0.0:
                    self.tilt = 0.0
                    self.finalize_tilting()
        # if right is heavier, increase tilt
        else:
            self.tilt += tilting_per_tick
            # check if finished tilting to the right
            if self.tilt >= 1.0:
                self.tilt = 1.0
                self.finalize_tilting()

    def finalize_tilting(self) -> None:
        self.moving = False
        game.playfield.refresh_status()

    def draw(self, surf: Surface) -> None:
        """Draw the two stacks onto surf"""

        blocked_height_left: float = 1.0 + self.tilt
        blockedcolor: Tuple[int, int, int] = (0, 0, 0)

        blocked_topleft: Tuple[int, int] = pixel_coord_in_playfield(
            (self.xleft, blocked_height_left - 1.0)
        )

        blocked_botright: Tuple[int, int] = pixel_coord_in_playfield((self.xleft, 0))

        blocked_botright[0] += ball_size[0]
        blocked_botright[1] += ball_size[1]
        width: int = blocked_botright[0] - blocked_topleft[0]
        height: int = blocked_botright[1] - blocked_topleft[1]

        # left side blocked
        draw_rect(surf, blockedcolor, Rect(blocked_topleft, (width, height)))
        # left stack of balls
        for y, ball in enumerate(self.stackleft):
            coords: Tuple[int, int] = pixel_coord_in_playfield(
                (self.xleft, 1 + self.tilt + y)
            )
            ball.draw(surf, coords)

        blocked_height_right: float = 1.0 - self.tilt
        blocked_topleft = pixel_coord_in_playfield(
            (self.xleft + 1, blocked_height_right - 1.0)
        )
        blocked_botright = pixel_coord_in_playfield((self.xleft + 1, 0))

        blocked_botright[0] += ball_size[0]
        blocked_botright[1] += ball_size[1]
        width = blocked_botright[0] - blocked_topleft[0]
        height = blocked_botright[1] - blocked_topleft[1]

        # right side blocked
        draw_rect(surf, blockedcolor, Rect(blocked_topleft, (width, height)))
        # right stack of balls
        for y, ball in enumerate(self.stackright):
            coords = pixel_coord_in_playfield((self.xleft + 1, 1 - self.tilt + y))
            ball.draw(surf, coords)

    def check_alive(self) -> bool:
        """False if a stack is high enough to trigger a game loss.
        Max allowed stack height depends on tilt: 6-8."""
        if self.ismoving():
            return True
        stackheight_left = len(self.stackleft)
        stackheight_right = len(self.stackright)
        if self.tilt == -1.0:
            return (
                stackheight_left <= max_height and stackheight_right <= max_height - 2
            )
        elif self.tilt == 0.0:
            return (
                stackheight_left <= max_height - 1
                and stackheight_right <= max_height - 1
            )
        else:
            return (
                stackheight_left <= max_height - 2 and stackheight_right <= max_height
            )

    def throw_top_ball(self) -> None:
        """if weights differ, throw top ball of lighter side.
        Weights are expected to already be updated"""
        weightdiff: int = self.weightright - self.weightleft
        if 0 == weightdiff:
            return
        if weightdiff > 0:
            lightstack = self.stackleft
            origin_x = self.xleft
            origin_y = round(self.landing_height(True)) - 1
        else:
            lightstack = self.stackright
            origin_x = self.xleft + 1
            origin_y = round(self.landing_height(False)) - 1
        if 0 == len(lightstack):
            return

        ongoing.throw_ball(lightstack.pop(), (origin_x, origin_y), weightdiff)

    def get_number_of_balls(self) -> int:
        """Returns total number of balls on both sides of the seesaw. Not
        counting falling Balls."""
        return len(self.stackleft) + len(self.stackright)

    def remove_ball_at(self, coords: Tuple[int, int]) -> None:
        """Remove a ball from specified position. Balls above the removed
        one are converted into FallingBalls.
        If there is no ball at coords, do nothing."""
        x, y = coords
        # x should be either self.xleft or self.xleft+1. If not,
        # this was called on the wrong seesaw.
        if x == self.xleft:
            stack = self.stackleft
            left = True
        elif x == self.xleft + 1:
            stack = self.stackright
            left = False
        else:
            raise ValueError("remove_ball_at called on wrong seesaw")
        if y < 0 or y > max_height + 1:
            raise ValueError("Can not remove Ball from that height." "coords=" + coords)

        blocked_height = self.get_blocked_height(left)
        # y -= blockedheight
        height_to_remove = round(y - blocked_height)

        if height_to_remove < 0 or height_to_remove >= len(stack):
            return

        # if not moving, this removes just one ball from the list.
        # Convert any above the removed one into FallingBalls

        stack.pop(height_to_remove)
        for height, ball in enumerate(
            stack[height_to_remove - 1 :]
        ):  # this iterates over a copy
            # so modifying is ok
            stack.remove(ball)
            ongoing.ball_falls_from_height(ball, x, height + blocked_height + 1)
        # if moving, do nothing for now.
        else:
            pass

    def remove_scored_balls(self, list_to_remove: list) -> None:
        """Remove marked balls that are in the list, drop hanging balls"""
        # left
        blocked_height: float = self.get_blocked_height(True)
        # bottom-up
        extra_height: int = 0
        for y, ball in enumerate(self.stackleft[:]):  # iterate over a copy
            # so modifying is ok
            if ball in list_to_remove:
                self.stackleft.remove(ball)
                extra_height += 1
            elif extra_height > 0:  # once something was removed, all above
                # must fall if not removed
                self.stackleft.remove(ball)
                ongoing.ball_falls_from_height(
                    ball, self.xleft, blocked_height + y + extra_height
                )

        # right
        blocked_height = self.get_blocked_height(False)
        # bottom-up
        extra_height = 0
        for y, ball in enumerate(self.stackright[:]):  # iterate over a copy
            if ball in list_to_remove:
                self.stackright.remove(ball)
                extra_height += 1
            elif extra_height > 0:
                self.stackright.remove(ball)
                ongoing.ball_falls_from_height(
                    ball, self.xleft + 1, blocked_height + y + extra_height
                )
