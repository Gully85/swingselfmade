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

from abc import abstractmethod
from typing import Tuple
import balls

import pygame
import game

from constants import ball_size, playfield_ballcoord, playfield_ballspacing, rowspacing
from constants import falling_per_tick, tilting_per_tick
from constants import thrown_ball_dropheight
from constants import explosion_numticks

import constants

# this is a local variable of the module ongoing. Other files, if they import this,
# can use and modify this. Their local name is ongoing.eventQueue
eventQueue = []

def tick():
    """perform update of all ongoing events. Called periodically as time passes."""
    for event in eventQueue:
        event.tick()

def reset():
    """empties eventQueue. This sets up the ongoing-module to the state of the game start"""
    global eventQueue
    eventQueue = []

def get_number_of_events():
    """Returns the number of currently ongoing events"""
    return len(eventQueue)

def get_oldest_event():
    """Returns the oldest event that is still ongoing. If there are none, raises IndexError"""
    return eventQueue[0]

def get_newest_event():
    """Returns the event that was added last and is still ongoing. If there are none, raises IndexError"""
    return eventQueue[-1]


class Ongoing:
    """abstract Parent class, should not be instanciated.
    Any child class must have a tick(self, playfield) method and a draw(self,surf) method."""
    
    @abstractmethod
    def tick(self):
        pass

    def draw(self, surf: pygame.Surface):
        pass

def event_type_exists(eventType):
    """True if at least one such event is currently ongoing"""
    for event in eventQueue:
        if isinstance(event, eventType):
            return True
    return False

def get_event_of_type(eventType):
    """Returns the oldest event of that type that is still ongoing.
    Raises GameStateError if None is there"""
    for event in eventQueue:
        if isinstance(event, eventType):
            return event
    raise game.GameStateError("Requested ongoing Event type ", eventType,
                                  "is not in the eventQueue.")

class FallingBall(Ongoing):
    """a Ball that is being dropped, falling after being thrown, or the Ball below it vanished somehow. Vars:
        ball (Colored_Ball or Special_Ball)
        column (int, 0..7)
        height (float, allowed range 8.0 >= height >= highest filled position in Playfield.content in respective column)
        
        Constructor: FallingBall(ball, col, starting_height=8.0). The starting height is optional, only to be used 
            if the Ball drops from Playfield instead of Crane/Thrown
        """
    
    def __init__(self, ball, column: int, starting_height=8.0):
        self.ball = ball
        self.column = column
        self.height = starting_height
        
    def draw(self, surf:pygame.Surface):
        x = playfield_ballcoord[0] + (self.column) * playfield_ballspacing[0]
        y = playfield_ballcoord[1] + (7.-self.height)*playfield_ballspacing[1]
        self.ball.draw(surf, (x,y))

    def tick(self):
        self.height -= falling_per_tick
        if self.height < game.playfield.landing_height_of_column(self.column):
            game.playfield.land_ball_in_column(self.ball, self.column)
            eventQueue.remove(self)
    
    def getheight(self):
        return self.height

    def getball(self):
        return self.ball
    
    def getcolumn(self):
        return self.column

def ball_falls(ball, column: int):
    eventQueue.append(FallingBall(ball, column))

def ball_falls_from_height(ball, column:int, height: int):
    eventQueue.append(FallingBall(ball, column, starting_height=height))

class ThrownBall(Ongoing):
    """A ball that was thrown by a seesaw. Follows a certain trajectory 
        (see comment in tick() for details), then becomes a FallingBall. Vars:
        ball (Colored_Ball or Special_Ball).
        destination (int), allowed range -1..8. Values 0..7 indicate landing in that column,
            Values -1 or 8 indicate flying out sideway. Destination height is always 8.2
        origin (int,int tuple), x and y coordinate of the spot from where it was launched. x=0..7, or
            -1 resp 8 if flying in from the side. 
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
    
    def __init__(self, ball, coords: Tuple[int], throwing_range: int):
        from constants import thrown_ball_maxheight
        self.ball = ball
        self.origin = coords
        self.x = float(coords[0])
        self.y = float(coords[1])
        if throwing_range == 0:
            raise ValueError("Attempting to throw ball ", ball, " from position ", coords, " with range zero.")
        
        # calculate destination. Three possible cases: Flying out left, landing in-bound, flying out right.
        destination_raw = coords[0] + throwing_range
        if destination_raw < 0: # fly out left
            self.destination = -1
            self.remaining_range = destination_raw + 1
        elif destination_raw > 8: # fly out right
            self.destination = 8
            self.remaining_range = destination_raw - 8
        else: # stay in-bound
            self.destination = destination_raw
            self.remaining_range = 0
        
        # the trajectory is parametrized with t going from -1 to +1
        self.t = -1.0
        
        self.speedup_pastmax = (thrown_ball_maxheight - self.origin[1]) / (thrown_ball_maxheight - thrown_ball_dropheight)
        
        print("Throwing ball ", ball, " from position ", coords, " with range ",
                throwing_range, ". Destination is ", self.destination, ", remaining is ", self.remaining_range)
        
        # Maybe generate the trajectory here, as a local lambda(t)?
    
    def getdestination(self):
        """Returns the destination of this ball-throwing event. Only x-coordinate. 
        Possible values are -1 .. 8. -1 for fly-out left, 0..7 for landing, 8 for fly-out right"""
        return self.destination

    def getball(self):
        """Returns the ball thrown"""
        return self.ball

    def getremaining_range(self):
        """Returns the remaining throwing range. 0 if landing in-bound, negative if going to fly-out to the left,
        positive if going to fly-out to the right"""
        return self.remaining_range
        
    def draw(self, surf):
        # identical to FallingBall.draw() so far
        x = playfield_ballcoord[0] + (self.x)*playfield_ballspacing[0]
        y = playfield_ballcoord[0] + (7. - self.y)*playfield_ballspacing[1]
        self.ball.draw(surf, (x,y))
        
    def tick(self):
        # increase t. If destination was reached (t>1), convert into a FallingBall or perform the fly-out.
        # If not, calculate new position x,y from the trajectory.
        from constants import thrown_ball_dt , thrown_ball_maxheight
        
        if self.t < 0:
            self.t += thrown_ball_dt
        else:
            self.t += thrown_ball_dt * self.speedup_pastmax
        game.playfield.changed()
        
        # is the destination reached? If yes, it can become a FallingBall or it can fly out
        if self.t > 1.0:
            if self.destination == -1 or self.destination == 8:
                self.fly_out(self.destination == -1)
            else:
                eventQueue.append(FallingBall(self.ball, self.destination, starting_height=thrown_ball_dropheight-2.0))
                eventQueue.remove(self)
        else:
            # Ball has not reached its destination yet. Update x and y of the trajectory.
            # The trajectory is a standard parabola -t**2. The t<0 side is for origin to max, 
            # t>0 arm for max to destination. t=-1 is origin, t=0 is max, t=1 is destination.
            # max is always at x=(origin+destination)/2, y=thrown_ball_maxheight
            # (That implies that the derivative is not smooth at the max. So be it.)
            maxx = (self.origin[0] + self.destination)/2
            maxy = thrown_ball_maxheight
            
            if self.t < 0.0:
                # t<0 origin side: t=0 is (maxx, maxy), t=-1 is origin
                self.x = maxx + self.t *  (maxx - self.origin[0])
                self.y = maxy - self.t**2*(maxy - self.origin[1])
            else:
                # t>0 destination side: Same thing with destination instead of origin
                self.x = maxx - self.t *  (maxx - self.destination)
                self.y = maxy - self.t**2*(maxy - thrown_ball_dropheight)
                
    
    def fly_out(self, left: bool):
        """Ball flew out to the left or right (indicated by argument). Insert it at the
            very right/left, set new origin, calculate and set new destination
        """
        # convert into Heart or Bomb
        if isinstance(self.ball, balls.SpecialBall) and not isinstance(self.ball, balls.Bomb):
            self.ball = balls.Bomb()
        else:
            self.ball = balls.Heart()

        from constants import thrown_ball_flyover_height, thrown_ball_maxheight
        self.t = -1.0
        self.y = thrown_ball_flyover_height
        if left:
            self.x = 8.0
        else:
            self.x = -1.0
        self.origin = (self.x, self.y)
        # calculate new destination. It can be another fly-out (if remaining_range is high enough) or a column.
        # Didn't find a way to make this shorter without losing readability...
        if left:
            if self.remaining_range < -8:
                self.destination = -1
                self.remaining_range += 8
            else: # in-bound
                self.destination = 7 + self.remaining_range  # self.remaining is negative
                self.remaining_range = 0
        else:
            if self.remaining_range > 7:
                self.destination = 8
                self.remaining_range -= 8
            else:
                self.destination = self.remaining_range
                self.remaining_range = 0
        
        self.speedup_pastmax = (thrown_ball_maxheight - self.origin[1]) / (thrown_ball_maxheight - thrown_ball_dropheight)
        print("Ball flying out, left=", left, ", new remaining_range=", self.remaining_range, 
            " and destination=", self.destination)


def throw_ball(ball, origin_coords: Tuple[int], throwing_range: int):
    """Throws ball from coords with specified range. origin_coords[0] = 0..7"""
    eventQueue.append(ThrownBall(ball, origin_coords, throwing_range))
    # print("throwing Ball, ", ball, origin_coords, throwing_range)


class Scoring(Ongoing):
    """Balls currently scoring points. Vars:
        past (list of [int,int], refers to coords in Playfield.content). Coords of all Balls that were already scored
        next (list of [int,int], refers to coords in Playfield.content). Coords of all Balls that should check their neighbors at next expand().
        color (int, corresponds to Ball.color)
        delay (int, counting down from scoring_delay. Number of ticks until Scoring will expand next)
        weight_so_far (int)
        
        Constructor: Scoring((x,y), ball)
    """
    
    def __init__(self, coords: Tuple[int], ball: balls.ScoringColoredBall):
        self.past = []   # list of ScoringColoredBalls
        self.next = [coords] # list of (int,int) coords in the playfield
        self.delay = constants.scoring_delay
        self.weight_so_far = ball.getweight()
        
    def draw(self, surf):
        # placeholder: Rectangles. Green (65,174,118) for past and slightly
        # brighter green (102,194,164) for next
        
        nextcolor = (102,194,164)

        #for (x,y) in self.past:
        #    xcoord = playfield_ballcoord[0] + x*playfield_ballspacing[0]
        #    ycoord = playfield_ballcoord[1] + (7-y)*playfield_ballspacing[1]
        #    pygame.draw.rect(surf, pastcolor, pygame.Rect((xcoord,ycoord), ball_size), width=3)
        
        for(x,y) in self.next:
            xcoord = playfield_ballcoord[0] + x*playfield_ballspacing[0]
            ycoord = playfield_ballcoord[1] + (7-y)*playfield_ballspacing[1]
            pygame.draw.rect(surf, nextcolor, pygame.Rect((xcoord,ycoord), ball_size), width=3)


    def tick(self):
        """called once per tick. Counts down delay, expands if zero was reached, and reset delay. 
        If no expansion, removes this from the eventQueue
        """
        
        import game
        self.delay -= 1
        if self.delay < 0:
            if self.expand():
                self.delay = constants.scoring_delay
            else:
                # Formula for Scores: Total weight x number of balls x level
                print("Score from this: ", self.weight_so_far * len(self.past) * game.level)
                game.score += self.weight_so_far * len(self.past) * game.level
                print("Total score: ", game.score)
                game.playfield.finalize_scoring(self.past)
                game.score_area.changed()
                eventQueue.remove(self)
                game.playfield.refresh_status()
                # TODO score and display

    def expand(self):
        """checks if neighboring balls are same color, removes them and saves their coords in 
        self.next for the next expand() call. Returns True if the Scoring grew.
        """

        now = self.next
        self.next = []
        #print("Expanding Scoring. Color=",color," past=",self.past, "now=",now)
        for coords in now:
            # TODO react properly if the Ball moved away from that position.
            marked_ball = game.playfield.mark_position_for_scoring(coords)
            self.past.append(marked_ball)
            
            x,y = coords
            coords_to_check = [(x-1,y), (x+1,y), (x,y-1), (x,y+1)]
            # remove out-of-bounds from this list
            for (x2,y2) in coords_to_check:
                if x2<0 or x2>7 or y2<0 or y2>8:
                    coords_to_check.remove((x2,y2))
            
            for (x2,y2) in coords_to_check:
                neighbor_ball = game.playfield.get_ball_at((x2,y2))
                if (neighbor_ball.matches_color(marked_ball) and
                not isinstance(neighbor_ball, balls.ScoringColoredBall)):
                    self.next.append([x2,y2])
                    self.weight_so_far += neighbor_ball.getweight()
                #if neighbor_ball.getcolor() == color:
                #    self.next.append([x2,y2])
                #    self.weight_so_far += game.playfield.get_ball_at((x2,y2)).getweight()
                #    game.playfield.remove_ball((x2,y2))

        #print("more matching Balls found: next=",self.next)
        game.playfield.changed()
        return len(self.next) > 0

def start_score(coords):
    #first_ball = game.playfield.mark_position_for_scoring(coords)
    first_ball = game.playfield.get_ball_at(coords)
    eventQueue.append(Scoring(coords, first_ball))

class Combining(Ongoing):
    """Balls from a vertical Five that combine into one ball with the total weight. 
    Once an animation is added to this, this class will make sense. For now, it only serves
    as a placeholder. Counts down for a few ticks, then dies. Drawing is just 'do nothing'. Vars:
        coords (tuple int,int), bottom coordinate where the resulting ball is placed.
        t (float), parameter that counts up from 0.0 to 1.0, tracks progress of the animation
        color (int), color of the resulting ball, as defined in the Colorscheme
        weight (int), weight of the resulting ball
    Constructor: Combining(coords, color, weight), coords is (int,int)
    """
    
    def __init__(self, coords:Tuple[int], color:int, weight:int):
        self.coords = coords
        self.color = color
        self.weight = weight
        self.t = 0.0

    def tick(self):
        from constants import combining_dt
        self.t += combining_dt
        if self.t > 1.0:
            eventQueue.remove(self)
            game.playfield.changed()
    
    def draw(self, surf):
        # draw an ellipse that contracts in y-direction over time
        from colorschemes import simple_standard_ball_colors
        the_color = simple_standard_ball_colors[self.color]
        starting_ysize = 5*ball_size[1] + 4*rowspacing
        final_ysize = ball_size[1]
        current_ysize = starting_ysize + self.t*(final_ysize-starting_ysize)
        xcoord = playfield_ballcoord[0] + self.coords[0]*playfield_ballspacing[0]
        ycoord_final = playfield_ballcoord[1] + (7-self.coords[1])*playfield_ballspacing[1]
        ycoord_start = playfield_ballcoord[1] + (7-self.coords[1]-4)*playfield_ballspacing[1]
        ycoord_now = ycoord_start + self.t*(ycoord_final-ycoord_start)

        px_coords = (xcoord, ycoord_now)
        pygame.draw.ellipse(surf, the_color, pygame.Rect(px_coords, (ball_size[0], current_ysize)))


    def getposition(self):
        """Position of the combining balls, where the resulting ball will be. Returned as a tuple (x,y)"""
        return self.coords

class Explosion(Ongoing):
    """A Bomb has recently exploded here, the sprite is drawn for a few frames."""

    def __init__(self, coords: Tuple[int]):
        self.coords = coords
        self.progress = 0.0
    
    def tick(self):
        self.progress += 1./explosion_numticks
        if self.progress > 1.0:
            eventQueue.remove(self)
    
    def draw(self, surf: pygame.Surface):
        pass

def draw_explosion(coords):
    eventQueue.append(Explosion(coords))
