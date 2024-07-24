# tests around the Crane class and module
# is imported indirectly via import game, testing game.crane

import sys

sys.path.append("S:/SwingSelfmade/")

from crane import Crane
from balls import Ball
from fallingball import FallingBall
import game
import unittest

from constants import num_columns


class TestTheCrane(unittest.TestCase):

    def test_crane_moves(self):
        game.reset()
        the_crane: Crane = game.crane

        the_crane.move_to_column(0)
        self.assertEqual(the_crane.getx(), 0)

        the_crane.move_right()
        self.assertEqual(the_crane.getx(), 1)

        the_crane.move_left()
        self.assertEqual(the_crane.getx(), 0)

    def test_crane_boundaries(self):
        """Assert that the crane can not move out of the boundaries. Possible columns are 0..7"""
        game.reset()
        the_crane: Crane = game.crane

        with self.assertRaises(ValueError):
            the_crane.move_to_column(-1)
        with self.assertRaises(ValueError):
            the_crane.move_to_column(num_columns)

        the_crane.move_to_column(0)
        the_crane.move_left()
        self.assertEqual(the_crane.getx(), 0)

        the_crane.move_to_column(7)
        the_crane.move_right()
        self.assertEqual(the_crane.getx(), num_columns - 1)

    def test_crane_has_ball(self):
        game.reset()
        the_crane: Crane = game.crane

        self.assertIsInstance(the_crane.getball(), Ball)

    def test_crane_drops_ball(self):
        """Drop a ball. Assert that the ball is falling in the EventQueue, and that
        the crane holds a different ball"""
        game.reset()
        the_crane: Crane = game.crane

        the_ball = the_crane.getball()
        the_crane.drop_ball()
        self.assertIsNot(the_crane.getball(), the_ball)

        fallingEvent: FallingBall = game.ongoing.get_event_of_type(FallingBall)
        self.assertIs(the_ball, fallingEvent.getball())


if __name__ == "__main__":
    unittest.main()
