# tests if the Game.init() sets everything up correctly

import unittest
import game, balls, constants
import pygame
import random


class Test_Game_Initialization(unittest.TestCase):

    def setUp(self):
        game.init()

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

    def test_depot(self):
        the_depot = game.depot
        
        # drop a ball of each depot row, verify type. Make sure out-of-bounds raises an IndexError
        for i in range(8): 
            self.assertIsInstance(the_depot.next_ball(i), balls.Ball)
        #self.assertRaises(the_depot.next_ball(8), IndexError)

        self.assertIsInstance(the_depot.draw(), pygame.Surface)

        # idea: force generation of a certain ball (once that's possible), it should fall out two drops later
    
    def test_game(self):
        # make sure the variables level, balls_dropped and score are there
        self.assertEqual(game.score, 0)
        self.assertEqual(game.balls_dropped, 0)
        self.assertEqual(game.level, 4)

        # drop 52 balls, check level and balls_dropped
        for i in range(52):
            game.drop_ball()
        self.assertEqual(game.balls_dropped, 52)
        self.assertEqual(game.level, 5)

    def test_ongoing_FallingBalls(self):
        self.assertEquals(0, game.ongoing.get_number_of_events())
        #self.assertRaises(game.ongoing.get_newest_event(), IndexError)
        #self.assertRaises(game.ongoing.get_oldest_event(), IndexError)

        testBall = balls.generate_ball()
        chosen_column = random.randint(0,7)
        game.ongoing.ball_falls(testBall, chosen_column)
        self.assertEquals(1, game.ongoing.get_number_of_events())
        self.assertIsInstance(game.ongoing.get_newest_event(), game.ongoing.FallingBall)

        the_falling_event = game.ongoing.eventQueue[0]
        # it should lose a bit of height over time
        initial_height = the_falling_event.height
        game.tick()
        game.tick()
        self.assertLess(the_falling_event.height, initial_height)

        # tick() for up to 10 ingame-seconds (that's 10*max_FPS ticks). Once it lands,
        # a SeesawTilting should start. Fail an assert if that doesn't happen within 10sec.
        for i in range(10*constants.max_FPS):
            game.tick()
            if isinstance(game.ongoing.eventQueue[0], game.ongoing.SeesawTilting):
                break
        self.assertLess(i, 10*constants.max_FPS) # if this fails, a dropped ball on an empty playfield
                                                 # did not start a SeesawTilting within 10 ingame-seconds.



if __name__ == '__main__':
    unittest.main()