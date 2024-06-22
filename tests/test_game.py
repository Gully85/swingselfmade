# test around the game class

import sys

sys.path.append("S:/SwingSelfmade/")

import game
from balls import Ball
from ongoing import FallingBall
import unittest


class TestTheGame(unittest.TestCase):

    def test_game_init(self):
        game.reset()

        self.assertEqual(0, game.score)
        self.assertEqual(0, game.balls_dropped)
        self.assertEqual(4, game.level)

    def test_game_levelup(self):
        game.reset()
        # drop 52 balls. Check length of eventQueue. Level should have increased by then.
        for i in range(52):
            game.drop_ball()

        self.assertEqual(5, game.level)

    def test_dropped_ball_in_eventQueue(self):
        game.reset()

        the_ball: Ball = game.crane.getball()
        game.drop_ball()

        event: FallingBall = game.ongoing.get_newest_event()
        self.assertIsInstance(event, FallingBall)
        self.assertEqual(event.getball(), the_ball)


if __name__ == "__main__":
    unittest.main()
