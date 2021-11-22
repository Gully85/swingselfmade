# provides the Playfield class. The playfield has 8 stacks of Balls 
# (lowest 0-2 are blocked, depending on seesaw state). An empty space in the playfield 
# is represented as None, same for a blocked space at the bottom.


debugprints = False

from typing import Tuple
from pygame import Rect, Surface, font
import balls, game
from balls import Blocked, NotABall, Colored_Ball, Special_Ball
#from game import GameStateError

import ongoing
from constants import playfield_ballcoord, playfield_ballspacing, weightdisplay_coords, weightdisplay_x_per_column


weightdisplayfont = font.SysFont("Arial", 12)

class Playfield:
    """Information about the current Playfield. Variables:
        content (8x9 array of either NotABall or Blocked or Balls). First index is column, second index height (bottom-up).
            At y=8 there should always be NotABall, else the player is about to lose the game.
        weights (8 ints, left to right). 
        seesaws (4 ints, left to right). 0 indicates equal 
            weights, -1 for heavier left, +1 for heavier right).
        size (2 ints). Size of drawing in px
        surf (pygame.Surface)
        alive (Bool). Indicates whether the game is lost.
    Constructor takes size in pixels as (width,height) tuple."""

    def __init__(self, size: Tuple[int]):
        self.content = []
        for i in range(8):
            self.content.append([ Blocked(),NotABall(),NotABall(),NotABall(), NotABall(),NotABall(),NotABall(),NotABall(),NotABall() ])
        
        self.weights = [0,0,0,0, 0,0,0,0]
        self.seesaws = [0,  0,   0,  0]
        self.size = size
        self.surf = Surface(size)
        self.changed = True # if anything changed since the last tick. Starts True so the initial gamestate is drawn.
        self.alive = True
    
    def reset(self):
        """puts the playfield into the state of game start"""
        self.weights = [0,0,0,0, 0,0,0,0]
        self.seesaws = [0,  0,   0,  0]
        self.content = []
        for i in range(8):
            self.content.append([ Blocked(),NotABall(),NotABall(),NotABall(), NotABall(),NotABall(),NotABall(),NotABall(),NotABall() ])
        self.changed = True
        self.alive = True
    
    def get_ball_at(self, coords: Tuple[int]):
        """Returns ball at position, or NotABall/Blocked if there is no ball at that position. Coords must 
        be (x,y) with x=0..7 and y=0..7
        Blocked is returned if that position is blocked by the seesaw state, only possible for y=0 or y=1"""
        x,y = coords
        if x<0 or x>7 or y<0 or y>7:
            raise IndexError("can't get Ball from position ({},{})".format(x,y))
        return self.content[x][y]
    
    def get_weight_of_column(self, column:int):
        """Returns total weight of the stack in given column 0..7."""
        self.update_weights()
        if column<0 or column>7:
            raise ValueError("Trying to get weight of column {}, only 0..7 possible".format(column))
        return self.weights[column]

    def check_alive(self):
        """True if all topmost positions in self.content are NotABall. Player loses if any stack gets too high"""
        for x in range(8):
            if not isinstance(self.content[x][8], NotABall):
                return False
        return True
    
    def land_ball(self, ball: balls.Ball, coords: Tuple[int]):
        """Land a ball at coords. Triggers a status update. x=0..7"""
        x,y = coords
        if isinstance(ball, Colored_Ball):
            self.content[x][y] = ball
            self.refresh_status()
        else:
            raise TypeError("Trying to land unexpected ball type ", ball, " at playfield position ", x, y)
        
    def land_ball_in_column(self, ball: balls.Ball, x: int):
        """Land a ball in specified column on top of the stack. x=0..7"""
        if x<0 or x>7:
            raise ValueError("Trying to land outside the playfield, column must be 0..7, given {}.".format(x))
        if not isinstance(ball, balls.Ball):
            raise TypeError("Trying to land something that is not a ball, given ", ball)
        
        # find lowest empty position, land ball there
        for y in range(8):
            if isinstance(self.get_ball_at((x,y)), balls.NotABall):
                self.land_ball(ball, (x, y))
                return
        
        # if no free position on top is available, just do nothing. This may change later. If this position
        # is reached, something landed on top of a full stack.
    
    def refresh_status(self):
        """Checks if anything needs to start now. Performs weight-check, 
        if that does nothing performs scoring-check, if that does nothing performs combining-check.
        """
        #print("Entering full status check...")

        if self.gravity_moves():
            #print("seesaw starts moving")
            pass
        elif self.check_Scoring_full():
            #print("found Scoring")
            pass
        elif self.check_combining():
        #	print("found vertical Five")
            pass
        elif self.check_hanging_balls():
            #print("dropping hanging ball(s)")
            pass
        elif not self.check_alive():
            self.alive = False

    
    def push_column(self, x: int, dy: int):
        """pushes the x-column down by (dy) and its connected neighbor up by (dy). x=0..7"""
        # x can be 0..7. Its neighbor is x+1 if x is even, and x+1 else.
        #neighbor = x+1 - 2*(x%2 == 0)
        neighbor = x-1 + 2*(x%2 == 0)
        self.raise_column(neighbor, dy)
        self.lower_column(x, dy)

    def lower_column(self, x: int, dy: int):
        """move all balls in a stack (dy) places down."""
        for height in range(0, 9-dy):
            self.content[x][height] = self.content[x][height + dy]
        # This will "duplicate" the NotABall on top of a stack. Is that a problem when 
        # it is later filled with an actual ball? I think not, but not 100% sure. A fix would be 
        # to create a new NotABall for y=8.

    def raise_column(self, x: int, dy: int):
        """moves all balls in a stack (dy) places up."""
        for height in range(8, dy-1, -1):
            self.content[x][height] = self.content[x][height - dy]

        for height in range(dy):
            self.content[x][height] = Blocked()

    def update_weights(self):
        """calculate all weights, saves results in self.weights"""
        for x in range(8):
            sum = 0
            for y in range(8):
                sum += self.content[x][y].weight
            self.weights[x]=sum
    
    def gravity_moves(self):
        """calculates all weights, compares with seesaw state, pushes if necessary, throws if necessary. 
        Returns True if any seesaw moved. Adds SeesawTilting and ThrownBall to the eventQueue if necessary.
        """
        self.update_weights()
        ret = False
        for sesa in range(4):
            left = 2*sesa
            right = 2*sesa+1
            oldstate = self.seesaws[sesa]
            # self.weights is off-by-one due to the dummy row [0].
            if self.weights[left] > self.weights[right]:
                newstate = -1
            elif self.weights[left] == self.weights[right]:
                newstate = 0
            else:
                newstate = 1
            if newstate == oldstate:
                continue
            
            # if this point is reached, the seesaw must start moving now. There are 
            # three cases: Sided to balanced, balanced to sided, one-sided to other-sided. 
            ongoing.tilt_seesaw(sesa, oldstate, newstate)
            self.seesaws[sesa] = newstate
            ret = True
            if newstate == 0:
                if oldstate == -1:
                    self.push_column(right, 1)
                else:
                    self.push_column(left, 1)
            elif newstate == -1:
                if oldstate == 0:
                    self.push_column(left, 1)
                else:
                    self.push_column(left, 2)
                self.throw_top_ball(right, self.weights[right] - self.weights[left])
            else:
                if oldstate == 0:
                    self.push_column(right, 1)
                else:
                    self.push_column(right, 2)
                self.throw_top_ball(left, self.weights[right] - self.weights[left])
            
        # when this point is reached, all seesaws have been checked and updated
        return ret
    
    def throw_top_ball(self, column: int, throwing_range: int):
        """throw the top ball of column. If there is no ball, do nothing. column=0..7"""
        # throwing can only happen if the column is already the high side of a seesaw. Can safely 
        # assume that y=0 and y=1 are Blocked. Remove this sanity check once tests look good.
        from game import GameStateError
        if not isinstance(self.content[column][0], Blocked) or not isinstance(self.content[column][1], Blocked):
            raise GameStateError("Trying to throw from a non-lifted seesaw side, x=", column)
        lastball = self.content[column][2]
        if isinstance(lastball, NotABall):
            return
        
        for y in range(3, 8):
            ball = self.content[column][y]
            if isinstance(ball, Blocked):
                raise GameStateError("A Blocked should never be this high. Blocked found at ({},{})".format(column, y))
            elif isinstance(ball, NotABall):
                ongoing.throw_ball(lastball, (column, y-1), throwing_range)
                self.content[column][y-1] = NotABall()
                self.weights[column] -= self.content[column][y-1].weight
                return
            else:
                lastball = ball

    def check_Scoring_full(self):
        """checks the full content for any horizontal-threes of the same color. 
        Adds a Scoring to the eventQueue if one was found.
        Returns True if a Scoring was found.
        Checks bottom-up, only the lowest row with a horizontal-three is checked, only the leftmost Three is found.
        """
        
        #print("Entering full scoring check")
        # x range 0..7, y range 1..7 can have valid horizontal-threes. These x,y loops look for the leftmost
        # Ball in a horizontal Three, so the x loop runs 1..6
        for y in range(1,8):
            for x in range(6):
                color = self.content[x][y].color
                if color == -1:
                    continue
                #print("non-empty color at (", x, ",", y, ")")
                if self.content[x+1][y].color != color:
                    continue
                #print("matching right neighbor (", x+1, ",", y, ")")
                if self.content[x+2][y].color == color:
                    print("Found Scoring")
                    ongoing.eventQueue.append(ongoing.Scoring((x,y), self.content[x][y]))
                    return True
        return False

    def check_hanging_balls(self):
        """checks the full playfield for balls that 'hang', i.e. no ball/Blocked below them.
        Convert them all into FallingBalls. Returns True if any were converted."""
        
        ret = False
        for x in range(8):
            # search highest position that can support a ball
            for y in range(0,9):
                current = self.content[x][y]
                if current.isBall or isinstance(current, Blocked):
                    continue
                elif isinstance(current, NotABall):
                    break
                else:
                    raise TypeError("in hanging-Balls check: Unexpected ball type ", current, "  at position ", x, y)
            air_height = y
            #print("in hanging-check: air-height=", air_height)
            for y in range(air_height, 8):
                current = self.content[x][y]
                if current.isBall:
                    ret = True
                    ongoing.eventQueue.append(ongoing.FallingBall(current, x, starting_height=y))
                    self.content[x][y] = NotABall()
                    #print("dropping hanging ball ", current, " from position", x, y)

        
        return ret

    def check_combining(self):
        """Checks the full gameboard for vertical Fives. Only one per stack is possible. 
        Combines if one is found, and creates an Ongoing.Combining. Returns True if any are found"""
        # feels like this could be written easier. Especially the thing in the check_height loop. 
        # @Chris, do you have an idea?
        ret = False
        
        #print("Entering full Combining check")
        for x in range(8):
            for y in range(0, 4):
                this_color = self.content[x][y].color
                if this_color == -1:
                    continue
                # if this point is reached, the current ball is a Colored_Ball. All others have the 
                # attribute color==-1
                total_weight = self.content[x][y].weight
                
                # five balls are needed: y, y+1, ..., y+4. If this loop reaches y+5, do not check 
                # the (y+5)-position, but Combine instead
                for check_height in range(y+1, y+6):
                    if check_height == y+5:
                        ret = True
                        self.content[x][y] = Colored_Ball(this_color, total_weight)
                        ongoing.eventQueue.append(ongoing.Combining((x,y), this_color, total_weight))
                        self.content[x][y+1] = NotABall()
                        self.content[x][y+2] = NotABall()
                        self.content[x][y+3] = NotABall()
                        self.content[x][y+4] = NotABall()
                        break
                    
                    if self.content[x][check_height].color != this_color:
                        break 
                    
                    total_weight += self.content[x][check_height].weight
        
        if (ret):
            self.check_hanging_balls()
        
        return ret
        
    def draw(self):
        """draws the Playfield including all Balls. Returns surface."""
        self.surf.fill((127,127,127))
        
        # draw all the Balls (and Blocked Positions), iterate over self.content
        for x in range(8):
            xcoord = playfield_ballcoord[0] + x*(playfield_ballspacing[0])
            for y in range(8):
                ycoord = playfield_ballcoord[1] + (7-y)*(playfield_ballspacing[1])
                if debugprints:
                    if isinstance(self.content[x][y], Blocked):
                        print("Blocked at pos {},{}".format(x,y))
                    elif isinstance(self.content[x][y], NotABall):
                        print("No Ball at pos {},{}".format(x,y))
                    elif isinstance(self.content[x][y], Colored_Ball):
                        print("Ball at pos {},{}".format(x,y))
                    else:
                        raise TypeError("In playfield at pos {},{} should be a Colored_Ball or NotABall or Blocked, instead there was {}.".format(x,y,self.content[x][y]))
                self.content[x][y].draw(self.surf, (xcoord, ycoord))
        # draw weightdisplay
        for x in range(8):
            weighttext = weightdisplayfont.render(str(self.weights[x]), True, (0,0,0))
            weightdisplay_x = weightdisplay_coords[0]
            weightdisplay_y = weightdisplay_coords[1]
            self.surf.blit(weighttext, (weightdisplay_x + x * weightdisplay_x_per_column, weightdisplay_y))
            
        return self.surf
    
    def get_seesaw_state(self, column: int):
        return self.seesaws[column]
    
    def remove_ball(self, coords:Tuple[int]):
        """remove a ball from specified position. If there is already no ball, do nothing. If the position
        is Blocked, raises GameStateError"""
        x,y = coords
        if x<0 or x>7 or y<0 or y>8:
            raise ValueError("Trying to remove ball from position "+coords+", that is out of bounds")

        ball_at_position = self.content[x][y]
        if isinstance(ball_at_position, balls.Blocked):
            raise game.GameStateError("Trying to remove ball from a Blocked position"+coords)

        self.content[x][y] = balls.NotABall()