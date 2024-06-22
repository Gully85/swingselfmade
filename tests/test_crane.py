# tests around the Crane class and module
# is imported indirectly via import game, testing game.crane

import sys
sys.path.append("S:/SwingSelfmade/")

from crane import Crane
import game, balls
import unittest

import sys
sys.path.append('..')

class TestTheCrane(unittest.TestCase):

    def test_crane_boundaries(self):
        """Assert that the crane can not move out of the boundaries. Possible columns are 0..7"""
        game.reset()
        the_crane: Crane = game.crane

        with self.assertRaises(ValueError):
            the_crane.move_to_column(-1)
        with self.assertRaises(ValueError):
            the_crane.move_to_column(8)
        
        the_crane.move_to_column(0)
        the_crane.move_left()
        self.assertEqual(the_crane.getx(), 0)

        the_crane.move_to_column(7)
        the_crane.move_right()
        self.assertEqual(the_crane.getx(), 7)
        
    def test_crane_moves(self):
        game.reset()
        the_crane = game.crane
        
        the_crane.move_to_column(0)
        self.assertEqual(the_crane.getx(), 0)

        the_crane.move_right()
        self.assertEqual(the_crane.getx(), 1)

        the_crane.move_left()
        self.assertEqual(the_crane.getx(), 0)


    def test_crane_has_ball(self):
        game.reset()
        the_crane = game.crane

        self.assertIsInstance(the_crane.getball(), balls.Ball)
        
    def test_crane_drops_ball(self):
        """Drop a ball. Assert that the ball is falling in the EventQueue, and that
        the crane holds a different ball"""
        game.reset()
        the_crane = game.crane

        the_ball = the_crane.getball()
        the_crane.drop_ball()
        self.assertNotEqual(the_crane.getball(), the_ball)

        fallingEvent: game.ongoing.FallingBall = game.ongoing.get_event_of_type(game.ongoing.FallingBall)
        self.assertEqual(the_ball, fallingEvent.getball())


if __name__ == '__main__':
    unittest.main()