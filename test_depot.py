# tests around the Depot class and module
# is imported indirectly via import game, testing game.depot

import game, balls
import unittest, random

class TestTheDepot(unittest.TestCase):
    def test_depot(self):
        game.reset()

        the_depot = game.depot

        # drop a ball out of the 8 rows 0..7, verify type. Make sure out-of-bounds raises an IndexError
        for i in range(8):
            self.assertIsInstance(the_depot.next_ball(i), balls.Ball)
        with self.assertRaises(IndexError):
            the_depot.next_ball(8)
        
        # TODO once ball generation can force a certain ball, check if it comes out exactly two drops later

if __name__ == '__main__':
    unittest.main()