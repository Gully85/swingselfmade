# tests the playfield module

import game
import unittest
import balls

class TestPlayfield(unittest.TestCase):
    def test_playfield(self):
        game.reset()

        the_playfield = game.playfield

        # at the beginning: The bottom row should be Blocked, the row 
        # above that should be NotABall, and check_hanging_balls() == False
        for i in range(8):
            self.assertIsInstance(the_playfield.get_ball_at((i,0)), balls.Blocked)
            self.assertIsInstance(the_playfield.get_ball_at((i,1)), balls.NotABall)
        self.assertFalse(the_playfield.check_hanging_balls())

        # generate random ball, land it to the very left, wait until eventQueue is empty.
        # Seesaw must be tilted to the left, the ball must be at coords (0,0), 
        # (1,0) and (1,1) must be Blocked
        Testball = balls.generate_starting_ball()
        the_playfield.land_ball_in_column(Testball, 0)
        while game.ongoing.get_number_of_events() != 0:
            game.tick()
        self.assertEqual(the_playfield.get_seesaw_state(0), -1)
        self.assertIs(the_playfield.get_ball_at((0,0)), Testball)
        self.assertIsInstance(the_playfield.get_ball_at((1,0)), balls.Blocked)
        self.assertIsInstance(the_playfield.get_ball_at((1,1)), balls.Blocked)

        # land a ball of equal weight in the neighboring column, wait for empty EventQueue,
        # should lead to balanced seesaws. Check that both balls are in the correct positions.
        Testball2 = balls.generate_ball()
        Testball2.setweight(Testball.getweight())
        the_playfield.land_ball_in_column(Testball2, 1)
        while game.ongoing.get_number_of_events() != 0:
            game.tick()
        self.assertEqual(the_playfield.get_seesaw_state(0), 0)
        self.assertIs(the_playfield.get_ball_at((0,1)), Testball)
        self.assertIs(the_playfield.get_ball_at((1,1)), Testball2)

        the_playfield.update_weights()
        self.assertEqual(the_playfield.get_weight_of_column(0), Testball.getweight())
        self.assertEqual(the_playfield.get_weight_of_column(1), Testball.getweight())




if __name__ == '__main__':
    unittest.main()