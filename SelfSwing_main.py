# main file, run this to start the game. Python must be installed, pygame package must be present

# Summary: perform init. While game is running, there is a long Event Loop. 
# It handles inputs and ongoing game mechanics, then waits to not exceed the FPS limit.
# Cycle this loop once per tick.
# Global variable "eventQueue" in the "ongoing" module, which is a list of everything moving while
#  time goes on (e.g. recently dropped Balls that have not yet touched the ground). 
# Each entry in there is of type "Ongoing", child-classes for the different types


import pygame
from pygame.locals import *

pygame.init()


from constants import max_FPS, screensize
from constants import depot_position, cranearea_position, playfield_position, scoredisplayarea_position

import game

game.init()

import balls

import ongoing


# used to ensure max number of ticks calculated per second
FrameLimiter = pygame.time.Clock()


def main():
    # init screen
    screen = pygame.display.set_mode(screensize)
    pygame.display.set_caption("Swing-Remake by Gully")
    
    # light-grey background for now
    background = pygame.Surface(screensize)
    background = background.convert()
    background.fill((217,217,217))
    
    # move everything to the screen
    screen.blit(background, (0,0))
    pygame.display.flip()
    
    # only a test, but doesn't hurt
    #Ongoing.eventQueue.append(Ongoing.FallingBall(Balls.generate_starting_ball(), 2))
    ongoing.drop_ball(balls.generate_starting_ball(), 2)
    
    
    # Event Loop
    while 1:
        ### Step 1, process user input
        for event in pygame.event.get():
            
            # end process when window is closed, or when Escape Key is pressed
            if event.type == QUIT:
                return
            # same when Escape Key is pressed
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    return
            
            # accepted user inputs: K_LEFT, K_RIGHT, K_DOWN, K_SPACE. Move crane left/right, but not past the boundaries
            if event.type == KEYDOWN:
                if event.key == K_LEFT:
                    game.crane.x -= 1
                    game.crane.changed = True
                    if game.crane.x < 0:
                        game.crane.x = 0
                if event.key == K_RIGHT:
                    game.crane.x += 1
                    game.crane.changed = True
                    if game.crane.x > 7:
                        game.crane.x = 7
                if event.key == K_DOWN or event.key == K_SPACE:
                    column = game.crane.x
                    ongoing.drop_ball(game.crane.current_Ball, column+1)
                    game.balls_dropped += 1
                    if game.balls_dropped % 50 == 0:
                        game.level += 1
                        game.score_area.update_level()
                    game.crane.current_Ball = game.depot.content[column][1]
                    game.depot.content[column][1] = game.depot.content[column][0]
                    game.depot.content[column][0] = balls.generate_ball()
                    # force re-draw of crane and depot
                    game.crane.changed = True
                    game.depot.changed = True
                    game.score_area.changed = True


        ## Step 2, proceed ongoing Events
        for event in ongoing.eventQueue:
            event.tick(game.playfield)
        
        ### Step 2.5, check if the player lost
        if not game.playfield.alive:
            print("Final score: ", game.score)
            break
        
        ### Step 3, update screen where necessary
        if game.depot.changed:
            drawn_depot = game.depot.draw()
            screen.blit(drawn_depot, depot_position)
            game.depot.changed = False
        
        if game.crane.changed:
            #print("Crane position: ",the_crane.x)
            drawn_crane = game.crane.draw()
            screen.blit(drawn_crane, cranearea_position)
            game.crane.changed = False
        
        if game.playfield.changed:
            game.playfield.update_weights()
            drawn_playfield = game.playfield.draw()
            for event in ongoing.eventQueue:
                event.draw(drawn_playfield)
            screen.blit(drawn_playfield, playfield_position)
            game.playfield.changed = False
        
        if game.score_area.changed:
            drawn_score_area = game.score_area.draw()
            screen.blit(drawn_score_area, scoredisplayarea_position)
            game.score_area.changed = False
        
        pygame.display.flip()
        
        
        # make sure the loop doesn't cycle faster than the FPS limit
        FrameLimiter.tick(max_FPS)

# execute main if this is the file called, not just imported
if __name__ == "__main__": main()