# tests if the Game.init() sets everything up correctly

import unittest
import game, balls
import pygame
import random

game.init()

class Test_Game_Initialization(unittest.TestCase):

    def test_depot(self):
        the_depot = game.depot
        
        # drop a ball of each depot row, verify type. Make sure out-of-bounds raises an IndexError
        for i in range(8): 
            self.assertIsInstance(the_depot.next_ball(i), balls.Ball)
        self.assertRaises(the_depot.next_ball(8), IndexError)

        self.assertIsInstance(the_depot.draw(), pygame.Surface)

        # idea: force generation of a certain ball (once that's possible), it should fall out two drops later
    
    def test_crane(self):
        the_crane = game.crane

        # move 20x in random direction (left or right), position must stay 0..7, get_ball must return a ball
        for i in range(20):
            if random.choice([True,False]):
                the_crane.move_left()
            else:
                the_crane.move_right()
            position = the_crane.getx()
            self.assertTrue(position >= 0 and position <= 7)
        self.assertIsInstance(the_crane.getball(), balls.Ball)

        # move all the way to the left, position must be 0 then
        for i in range(7):
            the_crane.move_left()
        self.assertEqual(the_crane.getx(), 0)
        # move all the way to the right, position must be 7 then
        for i in range(7):
            the_crane.move_right()
        self.assertEqual(the_crane.getx(), 7)
    
if __name__ == '__main__':
    unittest.main()