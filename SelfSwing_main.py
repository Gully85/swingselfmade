# main file, run this to start the game. Python must be installed, pygame package must be present

# Pattern: perform init. While game is running, there is a long Event Loop. 
# It handles inputs and ongoing game mechanics. Cycle this loop once per tick.
# Global variable "ongoing", which is a list of everything moving while time goes on (e.g. 
# recently dropped Balls that have not yet touched the ground). 
# Each entry in there is of type "Ongoing", child-classes for the different types

# TODO: Playfield.check_Scoring() und Ongoing.SeesawTilting testen

import pygame
from pygame.locals import *

pygame.init()

#from Constants import *
#from Constants import falling_per_tick, max_FPS
#from Constants import screensize, depotsize, craneareasize, playfieldsize
#from Constants import depot_position, cranearea_position, playfield_position

from Constants import max_FPS, screensize
from Constants import depot_position, cranearea_position, playfield_position, scoredisplayarea_position

import Game

Game.init()

#import Depot

import Balls

#import Crane

#import Playfield

import Ongoing


# (max) number of ticks occuring per second
FrameLimiter = pygame.time.Clock()



	
# initialize depot
#the_depot = Depot.Depot(depotsize)

# initialize crane
#the_crane = Crane.Crane(craneareasize)

# initialize playfield
#the_playfield = Playfield.Playfield(playfieldsize)

# test
#the_playfield.content[3][3] = bal.generate_starting_Ball()
#print(the_playfield.content[3][3])



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
	Ongoing.drop_ball(Balls.generate_starting_ball(), 2)
	
	
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
					Game.crane.x -= 1
					Game.crane.changed = True
					if Game.crane.x < 0:
						Game.crane.x = 0
				if event.key == K_RIGHT:
					Game.crane.x += 1
					Game.crane.changed = True
					if Game.crane.x > 7:
						Game.crane.x = 7
				if event.key == K_DOWN or event.key == K_SPACE:
					column = Game.crane.x
					Ongoing.drop_ball(Game.crane.current_Ball, column+1)
					Game.balls_dropped += 1
					if Game.balls_dropped % 50 == 0:
						Game.level += 1
						Game.score_area.update_level()
					Game.crane.current_Ball = Game.depot.content[column][1]
					Game.depot.content[column][1] = Game.depot.content[column][0]
					Game.depot.content[column][0] = Balls.generate_ball()
					# force re-draw of crane and depot
					Game.crane.changed = True
					Game.depot.changed = True
					Game.score_area.changed = True


		## Step 2, proceed ongoing Events
		for event in Ongoing.eventQueue:
			event.tick(Game.playfield)
		
		### Step 2.5, check if the player lost
		if not Game.playfield.check_alive():
			print("Final score: ", Game.score)
			break
		
		### Step 3, update screen where necessary
		if Game.depot.changed:
			drawn_depot = Game.depot.draw()
			screen.blit(drawn_depot, depot_position)
			Game.depot.changed = False
		
		if Game.crane.changed:
			#print("Crane position: ",the_crane.x)
			drawn_crane = Game.crane.draw()
			screen.blit(drawn_crane, cranearea_position)
			Game.crane.changed = False
		
		if Game.playfield.changed:
			Game.playfield.update_weights()
			drawn_playfield = Game.playfield.draw()
			for event in Ongoing.eventQueue:
				event.draw(drawn_playfield)
			screen.blit(drawn_playfield, playfield_position)
			Game.playfield.changed = False
		
		if Game.score_area.changed:
			drawn_score_area = Game.score_area.draw()
			screen.blit(drawn_score_area, scoredisplayarea_position)
			Game.score_area.changed = False
		
		pygame.display.flip()
		
		
		# make sure the loop doesn't cycle faster than the FPS limit
		FrameLimiter.tick(max_FPS)

# execute main if this is the file called, not just imported
if __name__ == "__main__": main()