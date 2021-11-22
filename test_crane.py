# tests around the Crane class and module
# is imported indirectly via import game, testing game.crane

import game, balls
import unittest, random

class TestTheCrane(unittest.TestCase):
    def test_crane(self):
        game.reset()
        
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

        # make sure the Ball in it (at start) is a ColoredBall
        currentBall = the_crane.getball()
        self.assertIsInstance(currentBall, balls.ColoredBall)

        # after dropping a ball, the newest item in the eventQueue must be a FallingBall
        the_crane.drop_ball()
        fallingEvent = game.ongoing.get_newest_event()
        self.assertIsInstance(fallingEvent, game.ongoing.FallingBall)

if __name__ == '__main__':
    unittest.main()