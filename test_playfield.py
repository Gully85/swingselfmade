# tests the playfield module

import game, constants
import unittest
import balls

class TestPlayfield(unittest.TestCase):
    def test_playfield(self):
        game.reset()

        the_playfield = game.playfield

        # at the beginning: The bottom row should be Blocked, the row 
        # above that should be EmptySpace, and check_hanging_balls() == False
        for i in range(8):
            self.assertIsInstance(the_playfield.get_ball_at((i,0)), balls.BlockedSpace)
            self.assertIsInstance(the_playfield.get_ball_at((i,1)), balls.EmptySpace)
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
        self.assertIsInstance(the_playfield.get_ball_at((1,0)), balls.BlockedSpace)
        self.assertIsInstance(the_playfield.get_ball_at((1,1)), balls.BlockedSpace)

        # land a ball of equal weight in the neighboring column, wait for empty EventQueue,
        # should lead to balanced seesaws. Check that both balls are in the correct positions.
        Testball2 = balls.generate_starting_ball()
        Testball2.setweight(Testball.getweight())
        the_playfield.land_ball_in_column(Testball2, 1)
        while game.ongoing.get_number_of_events() != 0:
            game.tick()
        self.assertEqual(the_playfield.get_seesaw_state(0), 0)
        self.assertIs(the_playfield.get_ball_at((0,1)), Testball)
        self.assertIs(the_playfield.get_ball_at((1,1)), Testball2)

        # Test get_weight_of_column
        the_playfield.update_weights()
        self.assertEqual(the_playfield.get_weight_of_column(0), Testball.getweight())
        self.assertEqual(the_playfield.get_weight_of_column(1), Testball.getweight())

    
    # Test all outcomes of refresh_status
    def test_refresh_status(self):
        game.reset()
        the_playfield = game.playfield

        # Tilting
        # Drop a ball to the rightmost column, should start a SeesawTilting
        Testball = balls.generate_ball()
        Testball.setweight(20)
        the_playfield.land_ball_in_column(Testball, 7)
        the_tilting_event = game.ongoing.get_newest_event()
        self.assertIsInstance(the_tilting_event, game.ongoing.SeesawTilting)
        self.assertEqual(the_tilting_event.getsesa(), 3)

        # Scoring
        game.reset()
        # Drop two heavy balls on the left side of each seesaw to create a flat ground
        for sesa in range(4):
            Testball = balls.generate_starting_ball()
            Testball.setweight(100)
            the_playfield.land_ball_in_column(Testball, 2*sesa)
            Testball = balls.generate_starting_ball()
            Testball.setweight(100)
            Testball.setcolor(1)
            the_playfield.land_ball_in_column(Testball, 2*sesa)
        
        self.assertTrue(wait_for_empty_eventQueue(10*constants.max_FPS))

        # put balls in the three leftmost columns. This should start a Scoring.
        for i in range(3):
            Testball2 = balls.generate_starting_ball()
            Testball2.setcolor(2)
            the_playfield.land_ball_in_column(Testball2, i)
        game.tick()
        self.assertIsInstance(game.ongoing.get_newest_event(), game.ongoing.Scoring)
        self.assertTrue(wait_for_empty_eventQueue(4*constants.scoring_delay))

        # same for the rightmost columns
        for i in range(5,8):
            Testball3 = balls.generate_starting_ball()
            Testball3.setcolor(3)
            the_playfield.land_ball_in_column(Testball3, i)
        game.tick()
        self.assertIsInstance(game.ongoing.get_newest_event(), game.ongoing.Scoring)
        self.assertTrue(wait_for_empty_eventQueue(4*constants.scoring_delay))

        # Combining
        # land 5 equal balls in column 4, they should combine
        for i in range(5):
            Testball4 = balls.generate_starting_ball()
            Testball4.setcolor(2)
            Testball4.setweight(3)
            the_playfield.land_ball_in_column(Testball4, 4)
        game.tick()
        self.assertIsInstance(game.ongoing.get_newest_event(), game.ongoing.Combining)
        self.assertTrue(wait_for_empty_eventQueue(constants.combining_totaltime * constants.max_FPS))
        # The resulting ball should be at position (4,2), color=2, weight=15
        resulting_ball = the_playfield.get_ball_at((4,2))
        self.assertIsInstance(resulting_ball, balls.ColoredBall)
        self.assertEqual(resulting_ball.getcolor(), 2)
        self.assertEqual(resulting_ball.getweight(), 15)

        # Hanging Balls
        # drop two balls in column 6, remove the lower one, assert that the higher one starts to fall
        Testball = balls.generate_starting_ball()
        the_playfield.land_ball_in_column(Testball, 6)
        Testball2 = balls.generate_starting_ball()
        the_playfield.land_ball_in_column(Testball2, 6)
        the_playfield.remove_ball((6,2))
        the_playfield.refresh_status()
        game.tick()

        # both positions should be empty now, newest Event should be FallingBall Testball2
        self.assertIsInstance(the_playfield.get_ball_at((6,2)), balls.EmptySpace)
        self.assertIsInstance(the_playfield.get_ball_at((6,3)), balls.EmptySpace)
        the_falling_event = game.ongoing.get_newest_event()
        self.assertIsInstance(the_falling_event, game.ongoing.FallingBall)
        self.assertEqual(the_falling_event.getcolumn(), 6)
        self.assertIs(the_falling_event.getball(), Testball2)
        

def wait_for_empty_eventQueue(maxticks: int):
    """Waits until the eventQueue is empty, up to specified number of ticks. Returns True
    if the eventQueue got empty."""
    maxticks = int(maxticks+1.0)
    for i in range(maxticks):
        game.tick()
        if 0 == game.ongoing.get_number_of_events():
            return True
    return False


if __name__ == '__main__':
    unittest.main()