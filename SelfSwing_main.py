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


from constants import (
    max_FPS,
    window_size,
    endlevel,
    endlevel_score_multiplier,
    balls_per_level,
    finalscore_y,
)


import game
from colorschemes import RGB_lightgrey, RGB_black

game.reset()


import balls


# used to ensure max number of ticks calculated per second
FrameLimiter = pygame.time.Clock()


def main():

    # print("The author thanks freepik.com for the pictograms used in this game.")

    # init screen
    global screen
    screen = pygame.display.set_mode(window_size)
    pygame.display.set_caption("Swing-Remake by Gully")

    # light-grey background for now
    background = pygame.Surface(window_size)
    background = background.convert()

    background.fill(RGB_lightgrey)

    # move everything to the screen
    screen.blit(background, (0, 0))
    pygame.display.flip()

    # Event Loop
    while 1:
        ### Step 1, process user input
        process_user_input()

        ### Step 1.5, auto-drop if no balls are Falling/Thrown atm
        if not game.ongoing.event_type_exists(game.ongoing.FallingBall) and (
            not game.ongoing.event_type_exists(game.ongoing.ThrownBall)
        ):
            game.drop_ball()

        ## Step 2, proceed ongoing Events
        game.tick()

        ### Step 2.5, check if the game ended
        if (
            game.getlevel() == endlevel - 1
            and game.balls_dropped % balls_per_level == balls_per_level - 1
        ):
            game.score = int(game.score * endlevel_score_multiplier)
            game.playfield.alive = False
        if not game.playfield.alive:
            finish_game(game.score)

        ### Step 3, update screen where necessary. TODO make this only one call, game.draw()
        game.depot.draw_if_changed(screen)
        game.crane.draw_if_changed(screen)
        game.playfield.draw_if_changed(screen)
        game.score_area.draw_if_changed(screen)

        # reveal new-drawn frame
        pygame.display.flip()

        # make sure the loop doesn't cycle faster than the FPS limit
        FrameLimiter.tick(max_FPS)


def finish_game(finalscore: int):
    import constants
    from colorschemes import RGB_red

    finalscore_pixelpos = (constants.scoredisplayarea_position_x, finalscore_y)
    finalscore_font = pygame.font.SysFont("Arial", 28)
    finalscore_text = finalscore_font.render(
        "Final Score: " + str(finalscore), True, RGB_red
    )
    global screen
    screen.blit(finalscore_text, finalscore_pixelpos)
    pygame.display.flip()
    while True:
        FrameLimiter.tick(max_FPS)
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                exit()


def process_user_input():
    for event in pygame.event.get():

        # end process when window is closed
        if event.type == QUIT:
            exit()
        # same when Escape Key is pressed
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                exit()

        # accepted user inputs: K_LEFT, K_RIGHT, K_DOWN, K_SPACE. Move crane left/right, but not past the boundaries
        if event.type == KEYDOWN:
            if event.key == K_LEFT:
                game.crane.move_left()
            if event.key == K_RIGHT:
                game.crane.move_right()
            if event.key == K_DOWN or event.key == K_SPACE:
                game.drop_ball()
            if event.key == K_b:
                balls.force_special("B")
            if event.key == K_c:
                balls.force_special("C")
            if event.key == K_h:
                balls.force_special("H")


# execute main if this is the file called, not just imported
if __name__ == "__main__":
    main()
