# provides the Playfield class. The playfield has 8 stacks of Balls 
# (lowest 0-2 are blocked, depending on seesaw state). An empty space in the playfield 
# is represented as None, same for a blocked space at the bottom.


debugprints = False

from typing import Tuple
#from pygame import Rect, Surface, font
import pygame
from pygame.transform import threshold
import balls, game
#from balls import BlockedSpace, EmptySpace, ColoredBall, SpecialBall
#from game import GameStateError

import ongoing
#from constants import playfield_ballcoord, playfield_ballspacing 
from constants import pixel_coord_in_playfield
from constants import weightdisplay_coords, weightdisplay_x_per_column
from constants import playfield_position
import constants


weightdisplayfont = pygame.font.SysFont("Arial", 12)

class Playfield:
    """Information about the current Playfield. 
    Constructor takes size in pixels as (width,height) tuple."""

    def __init__(self, size: Tuple[int]):

        self.stacks = [Seesaw(0), Seesaw(2), Seesaw(4), Seesaw(6)]

        self.size = size
        self.surf = pygame.Surface(size)
        self.redraw_needed = True
        self.alive = True
    
    def print_tilts(self):
        tilt1 = self.stacks[0].gettilt()
        tilt2 = self.stacks[1].gettilt()
        tilt3 = self.stacks[2].gettilt()
        tilt4 = self.stacks[3].gettilt()
        print(tilt1, tilt2, tilt3, tilt4)
    
    def print_seesaw_states(self):
        cols = []
        for i in range(8):
            cols.append(self.get_seesaw_state(i))
        print(cols)

    def tick(self):
        for sesa in self.stacks:
            sesa.tick()

    def reset(self):
        self.__init__(self.size)
    
    def changed(self):
        """trigger a redraw"""
        self.redraw_needed = True
    
    def draw_if_changed(self, screen: pygame.Surface):
        """draws Playfield if it changed or if any event is ongoing"""
        # draw if self.redraw_needed is set, or if any event is ongoing,
        # or if any stack is moving

        trigger_redraw = self.redraw_needed
        trigger_redraw |= game.ongoing.get_number_of_events() > 0
        for sesa in self.stacks:
            trigger_redraw |= sesa.ismoving()
        
        if not trigger_redraw:
            return
        else:
            drawn_playfield = self.draw()
            for event in game.ongoing.eventQueue:
                event.draw(drawn_playfield)
            screen.blit(drawn_playfield, playfield_position)
            self.redraw_needed = False

    def draw(self):
        """draws the Playfield including all Balls. Returns surface."""
        self.surf.fill((127,127,127))
        
        for x in range(4):
            self.stacks[x].draw(self.surf)
        #self.stacks[0].draw(self.surf)

        # draw weightdisplay
        #for x in range(8):
        #    weighttext = weightdisplayfont.render(str(self.weights[x]), True, (0,0,0))
        #    weightdisplay_x = weightdisplay_coords[0]
        #    weightdisplay_y = weightdisplay_coords[1]
        #    self.surf.blit(weighttext, (weightdisplay_x + x * weightdisplay_x_per_column, weightdisplay_y))
            
        return self.surf

    def get_ball_at(self, coords: Tuple[int]):
        """Returns ball at position, or EmptySpace/Blocked if there is no ball at that position. Coords must 
        be (x,y) with x=0..7 and y=0..7
        Blocked is returned if that position is blocked by the seesaw state, only possible for y=0 or y=1"""
        x,y = coords
        if x<0 or x>7 or y<0 or y>7:
            raise IndexError("can't get Ball from position ({},{})".format(x,y))

        return self.stacks[x//2].get_ball_at_height(y, x%2==0)

    
    def get_weight_of_column(self, column:int):
        """Returns total weight of the stack in given column 0..7."""
        if column<0 or column>7:
            raise ValueError("Trying to get weight of column {}, "
                             "only 0..7 possible".format(column))
        
        x = column//2 # 0..3 possible
        sesa = self.stacks[x]
        sesa.update_weight()
        return sesa.getweight(x%2==0)

    def check_alive(self):
        """False if any stack is too high. Max 6-8 balls per stack are allowed,
        depending on seesaw tilt position. Moving seesaws never trigger a loss"""
        for sesa in self.stacks:
            if not sesa.check_alive():
                return False
        return True
    
    def land_ball(self, ball: balls.Ball, coords: Tuple[int]):
        """Land a ball at coords. Triggers a status update. x=0..7"""
        x = coords[0]
        sesa = self.stacks[x//2]
        sesa.land_ball(x%2==0, ball)
        
    def land_ball_in_column(self, ball: balls.Ball, x: int):
        """Land a ball in specified column on top of the stack. x=0..7"""
        sesa = self.stacks[x//2]
        sesa.land_ball(x%2==0, ball)
    
    def refresh_status(self):
        """Checks if anything needs to start now. Performs weight-check, 
        if that does nothing performs scoring-check, if that does nothing performs combining-check.
        """

        if not self.gravity_moves():
            if not self.check_Scoring_full():
                self.check_combining()
        
        if not self.check_alive():
            self.alive = False

    def update_weights(self):
        """updates all weights"""
        for sesa in self.stacks:
            sesa.update_weight()
    
    def gravity_moves(self):
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
    
    def any_seesaw_is_moving(self):
        """True if at least one of the seesaws is moving."""
        for stack in self.stacks:
            if stack.ismoving():
                return True
        return False
    
    def check_Scoring_full(self):
        """checks the full content for any horizontal-threes of the same color. 
        Adds a Scoring to the eventQueue if one was found.
        Returns True if a Scoring was found.
        Checks bottom-up, only the lowest row with a horizontal-three is checked, only the leftmost Three is found.
        """

        # lowest row can never Score. Start at height 1
        for y in range(1,8):
            for x in range(1,7): # x=1..6 makes sure that (x +/- 1) stays in-bound 0..7
                the_ball = self.get_ball_at((x,y))
                if not isinstance(the_ball, balls.Ball):
                    continue
                
                # TODO check Joker, Heart, Star

                left_neighbor = self.get_ball_at((x-1,y))
                if not left_neighbor.matches_color(the_ball):
                    continue
                right_neighbor = self.get_ball_at((x+1,y))
                if right_neighbor.matches_color(the_ball):
                    ongoing.start_score((x,y))
                    return True
        return False

    def check_combining(self):
        """Checks the full gameboard for vertical Fives. Only one per stack is possible. 
        Combines if one is found, and creates an Ongoing.Combining. Returns True if any are found"""
        return False
        # obsolete code below
        #print("Entering full Combining check")
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
                for check_height in range(y+1, y+6):
                    if check_height == y+5:
                        ret = True
                        self.content[x][y] = ColoredBall(this_color, total_weight)
                        ongoing.eventQueue.append(ongoing.Combining((x,y), this_color, total_weight))
                        self.content[x][y+1] = EmptySpace()
                        self.content[x][y+2] = EmptySpace()
                        self.content[x][y+3] = EmptySpace()
                        self.content[x][y+4] = EmptySpace()
                        break
                    
                    if self.content[x][check_height].getcolor() != this_color:
                        break 
                    
                    total_weight += self.content[x][check_height].getweight()
        
        if ret:
            self.check_hanging_balls()
            self.changed()
        
        return ret
    
    def mark_position_for_scoring(self, coords: Tuple[int]):
        """Converts Ball at position to ScoringColoredBall, return the resulting one"""
        x,y = coords
        return self.stacks[x//2].mark_position_for_scoring(coords)
    
    def finalize_scoring(self, balls: list):
        """Remove all the (marked) balls supplied"""
        for sesa in self.stacks:
            sesa.remove_scored_balls(balls)

    
    def get_number_of_balls(self):
        """Returns the number of balls currently lying in the playfield. Not counting FallingBalls
        or ThrownBalls."""
        ret = 0
        for sesa in self.stacks:
            ret += sesa.get_number_of_balls()

        return ret
    
    def get_seesaw_state(self, column: int):
        """Returns current tilt status of column (0..7) as int. -1, 0 or +1 for
        low, balanced, high. If moving, rounded towards nearest position."""
        sesa = self.stacks[column//2]
        raw_tilt = sesa.gettilt()
        left = column%2 == 0
        # tilt is -1 for heavier left and +1 for heavier right. Right is negative raw_tilt
        if left:
            return round(raw_tilt)
        else:
            return round(-raw_tilt)
    
    def remove_ball(self, coords:Tuple[int]):
        """remove a ball from specified position. If there is already no ball, do nothing. If the position
        is Blocked, raises GameStateError"""
        x,y = coords
        if x<0 or x>7 or y<0:
            raise ValueError("Trying to remove ball from position "+coords+", that is out of bounds")

        sesa = self.stacks[x//2]
        sesa.remove_ball_at(coords)

    def landing_height_of_column(self, column: int):
        """Returns the height of the lowest EmptySpace position of a column. Possible values are 1..8"""
        sesa = self.stacks[column//2]
        return sesa.landing_height(column%2==0)

class Seesaw:
    """A pair of two connected stacks in the playfield."""
    def __init__(self, xleft):
        self.tilt = 0.0 # 0 for balanced, #-1 for heavier left
                        # side, +1 for heavier right side
        self.weightleft = 0
        self.weightright = 0
        self.stackleft = [] # first is lowest, last is highest Ball
        self.stackright = [] # first is lowest, last is highest Ball
        self.moving = False
        self.xleft = xleft
    
    def ismoving(self):
        return self.moving
    
    def landing_height(self, left: bool):
        blockedheight = self.get_blocked_height(left)
        if left:
            return blockedheight + len(self.stackleft)
        else:
            return blockedheight + len(self.stackright)
    
    def explode_bombs(self, left:bool):
        """If the stack is not moving and contains bombs,
        trigger their explosion"""
        if self.ismoving():
            return
        
        if left:
            stack = self.stackleft
        else:
            stack = self.stackright
        blockedheight = self.get_blocked_height(left)
        for y,ball in enumerate(stack):
            if isinstance(ball, balls.Bomb):
                ball.explode((self.xleft+(1-left), y+blockedheight))

    def land_ball(self, left: bool, ball: balls.Ball):
        game.playfield.changed()
        y = self.landing_height(left)
        if left:
            stack = self.stackleft
            stack.append(ball)
            self.weightleft += ball.getweight()
            x = self.xleft
        else:
            stack = self.stackright
            stack.append(ball)
            self.weightright += ball.getweight()
            x = 1 + self.xleft
        
        # trigger on-landing effect of SpecialBall
        if isinstance(ball, balls.SpecialBall):
            if 1 == len(stack):
                ball.landing_effect_on_ground((x,y))
            else:
                ball.landing_effect_on_ball((x,y))
        elif isinstance(ball, balls.ColoredBall):
            pass
        else:
            from game import GameStateError
            raise GameStateError("Trying to land "
                                "unexpected Ball type", ball)

        # TODO throwing (only if ColoredBall). Or do
        # this in playfield.refresh_status()?

        game.playfield.refresh_status()
        
    def check_gravity(self):
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

    def getweight(self, left: bool):
        """Weight of one stack."""
        if left:
            return self.weightleft
        else:
            return self.weightright
    
    def gettilt(self):
        """-1 for heavier left, 0 for balanced, 
        +1 for heavier right. Can have any float value 
        between -1.0 and +1.0."""
        return self.tilt

    def get_ball_at_height(self, height: int, left: bool):
        # TODO what if moving? Both? Return Dummy object?
        if left:
            stack = self.stackleft
        else:
            stack = self.stackright
        blockedheight = round(self.get_blocked_height(left))
        if height < blockedheight:
            return balls.BlockedSpace()
        elif height >= blockedheight + len(stack):
            return balls.EmptySpace()
        else:
            return stack[height-blockedheight]
    
    def get_blocked_height(self, left: bool):
        """Returns the number of blocked space at the bottom as float. 
        Must be round()'ed to get integer 0,1,2"""
        if left:
            return 1.0 + self.tilt
        else:
            return 1.0 - self.tilt

    def update_weight(self):
        """calculates total weight of both sides, 
        updates internal weight variable"""
        self.weightleft = 0
        for ball in self.stackleft:
            self.weightleft += ball.getweight()
        self.weightright = 0
        for ball in self.stackright:
            self.weightright += ball.getweight()

    def tick(self):
        """if moving, tilt further. Check if tilting is done."""
        if not self.moving:
            return
        
        # if left is heavier, reduce tilt
        if self.weightleft > self.weightright:
            self.tilt -= constants.tilting_per_tick
            if self.tilt <= -1.0:
                self.tilt = -1.0
                self.finalize_tilting()
        # if weights are equal, move tilt towards zero
        elif self.weightleft == self.weightright:
            if self.tilt > 0.0:
                self.tilt -= constants.tilting_per_tick
                if self.tilt <= 0.0:
                    self.tilt = 0.0
                    self.finalize_tilting()
            else:    
                self.tilt += constants.tilting_per_tick
                if self.tilt >= 0.0:
                    self.tilt = 0.0
                    self.finalize_tilting()
        # if right is heavier, increase tilt
        else:
            self.tilt += constants.tilting_per_tick
            # check if finished tilting to the right
            if self.tilt >= 1.0:
                self.tilt = 1.0
                self.finalize_tilting()

    def finalize_tilting(self):
        self.moving = False
        game.playfield.refresh_status()
    
    def draw(self, surf: pygame.Surface):
        """Draw the two stacks onto surf"""
        
        blocked_height_left = 1.0 + self.tilt
        blockedcolor = (0,0,0)

        #print("tilt:", self.tilt)
        #print("left")
        blocked_topleft = pixel_coord_in_playfield((self.xleft, blocked_height_left-1.0))
        #print("topleft: ", blocked_topleft)
        blocked_botright = pixel_coord_in_playfield((self.xleft, 0))
        #print("botright: ", blocked_botright)
        blocked_botright[0] += constants.ball_size[0]
        blocked_botright[1] += constants.ball_size[1]
        width = blocked_botright[0] - blocked_topleft[0]
        height = blocked_botright[1]- blocked_topleft[1]
        #print(height)

        # left side blocked
        pygame.draw.rect(surf, blockedcolor, pygame.Rect(blocked_topleft, (width, height)))
        # left stack of balls
        for y,ball in enumerate(self.stackleft):
            coords = pixel_coord_in_playfield((self.xleft, 1+self.tilt+y))
            ball.draw(surf, coords)
        
        blocked_height_right = 1.0 - self.tilt
        blocked_topleft = pixel_coord_in_playfield((self.xleft+1, blocked_height_right-1.0))
        blocked_botright = pixel_coord_in_playfield((self.xleft+1, 0))

        blocked_botright[0] += constants.ball_size[0]
        blocked_botright[1] += constants.ball_size[1]
        width = blocked_botright[0] - blocked_topleft[0]
        height= blocked_botright[1] - blocked_topleft[1]

        # right side blocked
        pygame.draw.rect(surf, blockedcolor, pygame.Rect(blocked_topleft, (width,height)))
        # right stack of balls
        for y,ball in enumerate(self.stackright):
            coords = pixel_coord_in_playfield((self.xleft+1, 1-self.tilt+y))
            ball.draw(surf, coords)

    def check_alive(self):
        """False if a stack is high enough to trigger a game loss.
        Max allowed stack height depends on tilt: 6-8."""
        if self.ismoving():
            return True
        stackheight_left = len(self.stackleft)
        stackheight_right= len(self.stackright)
        if self.tilt == -1.0:
            return stackheight_left <= 8 and stackheight_right <= 6
        elif self.tilt == 0.0:
            return stackheight_left <= 7 and stackheight_right <= 7
        else:
            return stackheight_left <= 6 and stackheight_right <= 8
    
    def throw_top_ball(self):
        """if weights differ, throw top ball of lighter side.
        Weights are expected to already be updated"""
        weightdiff = self.weightright - self.weightleft
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
        
    def get_number_of_balls(self):
        """Returns total number of balls on both sides of the seesaw. Not 
        counting falling Balls."""
        return len(self.stackleft) + len(self.stackright)
    
    def remove_ball_at(self, coords: Tuple[int,int]):
        """Remove a ball from specified position. Balls above the removed
        one are converted into FallingBalls.
        If there is no ball at coords, do nothing. If that position is
        Blocked, raise GameStateError. If the seesaw is currently moving,
        this can remove two balls.
        """
        x,y = coords
        # x should be either self.xleft or self.xleft+1. If not, 
        # this was called on the wrong seesaw.
        if not (x == self.xleft or x == self.xleft+1):
            raise ValueError("remove_ball_at(", coords
            ,") called on wrong seesaw")
        if y < 0 or y > 9:
            raise ValueError("Can not remove Ball from that height."
                             "coords="+coords)
        left = (x%2 == 0)
        if left:
            stack = self.stackleft
        else:
            stack = self.stackright
        blockedheight = self.get_blocked_height(left)
        y -= blockedheight
        if y >= len(stack):
            return
        
        # if not moving, this removes just one ball from the list. 
        # Convert any above the removed one into FallingBalls
        if not self.ismoving():
            stack.pop(y)
            for height,ball in enumerate(stack[y:]):
                stack.remove(ball)
                ongoing.ball_falls_from_height(ball, x, height+blockedheight+1)
        # if moving, do nothing for now.
        else:
            pass
    
    def mark_position_for_scoring(self, coords: Tuple[int,int]):
        """Converts Ball at position to ScoringColoredBall, return the resulting one"""
        x,y = coords
        left = (x%2 == 0)
        if left:
            stack = self.stackleft
            blocked_height = round(1.0 + self.tilt)
        else:
            stack = self.stackright
            blocked_height = round(1.0 - self.tilt)
        y -= blocked_height
        old_ball = stack[y]
        new_ball = old_ball.mark_for_Scoring()
        stack[y] = new_ball
        return new_ball

    def remove_scored_balls(self, list_to_remove: list):
        """Remove marked balls that are in the list, drop hanging balls"""
        # TODO correct drop-heights
        # left
        blocked_height = self.get_blocked_height(True)
        # bottom-up
        extra_height = 0
        for y,ball in enumerate(self.stackleft[:]): # iterate over a copy
                                                    # so modifying is ok
            if ball in list_to_remove:
                self.stackleft.remove(ball)
                extra_height += 1
            elif extra_height > 0:  # once something was removed, all above
                                    # must fall if not removed
                self.stackleft.remove(ball)
                ongoing.ball_falls_from_height(ball, self.xleft, 
                                blocked_height + y + extra_height)
        
        # right
        blocked_height = self.get_blocked_height(False)
        # bottom-up
        extra_height = 0
        for y,ball in enumerate(self.stackright[:]): # iterate over a copy
            if ball in list_to_remove:
                self.stackright.remove(ball)
                extra_height += 1
            elif extra_height > 0:
                self.stackright.remove(ball)
                ongoing.ball_falls_from_height(ball, self.xleft+1,
                                blocked_height + y + extra_height)


        
        # right
        blocked_height = self.get_blocked_height(False)
        # bottom-up
        for ball in self.stackright:
            if ball in list_to_remove:
                self.stackright.remove(ball)
        

                