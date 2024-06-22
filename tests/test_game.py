# test around the game class

import sys
sys.path.append("S:/SwingSelfmade/")

import game
import unittest

class TestTheGame(unittest.TestCase):
    def test_game(self):
        game.reset()

        # check initial values of score etc
        self.assertEqual(0, game.score)
        self.assertEqual(0, game.balls_dropped)
        self.assertEqual(4, game.level)

        # drop 52 balls. Check length of eventQueue. Level should have increased by then.
        for i in range(52):
            game.drop_ball()
        self.assertEqual(52, game.ongoing.get_number_of_events())
        self.assertIsInstance(game.ongoing.get_newest_event(), game.ongoing.FallingBall)

if __name__ == '__main__':
    unittest.main()