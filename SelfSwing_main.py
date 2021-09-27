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


from Constants import *


import Depot as dep

import Balls as bal

import Crane as cra

import Playfield as pla

import Ongoing as ong


# (max) number of ticks occuring per second
FrameLimiter = pygame.time.Clock()

# Warn if falling Speed is higher than one tile per tick. This could break the FallingBall mechanic
if falling_per_tick > 1.0:
	print("Falling Speed too high. Do not fall more than one tile per tick.")

	
# initialize depot
the_depot = dep.Depot(depotsize)

# initialize crane
the_crane = cra.Crane(craneareasize)

# initialize playfield
the_playfield = pla.Playfield(playfieldsize)

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
	
	ongoing_Events = []
	ongoing_Events.append(ong.FallingBall(bal.generate_starting_ball(), 2))
	
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
					the_crane.x -= 1
					the_crane.changed = True
					if the_crane.x < 0:
						the_crane.x = 0
				if event.key == K_RIGHT:
					the_crane.x += 1
					the_crane.changed = True
					if the_crane.x > 7:
						the_crane.x = 7
				if event.key == K_DOWN or event.key == K_SPACE:

					column = the_crane.x
					ongoing_Events.append(ong.FallingBall(the_crane.current_Ball, column+1))
					the_crane.current_Ball = the_depot.content[column][1]
					the_depot.content[column][1] = the_depot.content[column][0]
					the_depot.content[column][0] = bal.generate_starting_ball()
					the_crane.changed = True
					the_depot.changed = True


		## Step 2, proceed ongoing Events
		#print (ongoing_Events)
		for event in ongoing_Events:
			event.tick(the_playfield, ongoing_Events)
		
		
		### Step 3, update screen where necessary
		
		if the_depot.changed:
			drawn_depot = the_depot.draw()
			screen.blit(drawn_depot, depot_position)
			the_depot.changed = False
		
		
		if the_crane.changed:
			#print("Crane position: ",the_crane.x)
			drawn_crane = the_crane.draw()
			screen.blit(drawn_crane, cranearea_position)
			the_crane.changed = False
		
		if the_playfield.changed:
			the_playfield.update_weights()
			drawn_playfield = the_playfield.draw()
			for event in ongoing_Events:
				event.draw(drawn_playfield)
			screen.blit(drawn_playfield, playfield_position)
			the_playfield.changed = False
		
		pygame.display.flip()
		
		
		# make sure the loop doesn't cycle faster than the FPS limit
		FrameLimiter.tick(max_FPS)

# execute main if this is the file called, not just imported
if __name__ == "__main__": main()