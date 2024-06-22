# tests around the Depot class and module
# is imported indirectly via import game, testing game.depot

import sys

sys.path.append("S:/SwingSelfmade/")

import game, balls
import unittest


class TestTheDepot(unittest.TestCase):

    def test_depot_number_of_rows(self):
        game.reset()

        the_depot = game.depot

        # Rows 0..7 must be able to drop a Ball
        for i in range(8):
            self.assertIsInstance(the_depot.next_ball(i), balls.Ball)

        # Rows -1 and 8 must raise an IndexError
        with self.assertRaises(IndexError):
            the_depot.next_ball(-1)
        with self.assertRaises(IndexError):
            the_depot.next_ball(8)

        # TODO once ball generation can force a certain ball, check if it comes out exactly two drops later


if __name__ == "__main__":
    unittest.main()
