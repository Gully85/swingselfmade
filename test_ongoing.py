# tests the ongoing module. Separate test_ method for each class in there

from unittest.case import TestCase
import game, balls, constants
import unittest, random



class TestOngoing(unittest.TestCase):
    def test_falling(self):
        game.reset()

        # create a random ball, drop it in a random column
        Testball = balls.generate_ball()
        chosen_column = random.randint(0,7)
        game.ongoing.ball_falls(Testball, chosen_column)
        self.assertEqual(1, game.ongoing.get_number_of_events())
        the_falling_event = game.ongoing.get_newest_event()
        self.assertIsInstance(the_falling_event, game.ongoing.FallingBall)
        
        # make sure it loses height over time
        self.assertIsInstance(the_falling_event.getball(), balls.Ball)
        starting_height = the_falling_event.getheight()
        game.tick()
        self.assertLess(game.ongoing.get_newest_event().getheight(), starting_height)

        # it should land after some time. Maximum number of ticks allowed is 8.0 / falling_speed * max_FPS
        # (it should only need to drop by 7 positions and then trigger a SeesawTilting, 8.0 leaves some room)
        maxticks = int(8.0 * constants.max_FPS / constants.falling_speed)
        self.assertGreater(maxticks, 0)
        for i in range(maxticks):
            game.tick()
            if the_falling_event is not game.ongoing.get_oldest_event():
                break
        self.assertLess(i, maxticks)
        self.assertIsInstance(game.ongoing.get_newest_event(), game.ongoing.SeesawTilting)
        
    def test_tilting(self):
        game.reset()

        # create a ball, land it
        Testball = balls.generate_ball()
        chosen_column = random.randint(0,8)
        chosen_seesaw = chosen_column//2
        game.playfield.land_ball_in_column(Testball, chosen_column)
        self.assertEqual(1, game.ongoing.get_number_of_events())
        the_tilting_event = game.ongoing.get_newest_event()
        self.assertIsInstance(the_tilting_event, game.ongoing.SeesawTilting)

        self.assertEqual(the_tilting_event.getsesa(), chosen_seesaw)

        # make sure progress increases per tick
        initial_progress = the_tilting_event.getprogress()
        game.tick()
        self.assertGreater(the_tilting_event.getprogress(), initial_progress)

        # it should remove itself after some time. Expected number of ticks is (1. / tilting_per_tick)
        maxticks = int(1./ constants.tilting_per_tick) + 1
        for i in range(maxticks):
            game.tick()
            if 0 == game.ongoing.get_number_of_events():
                break
            if isinstance(game.ongoing.get_newest_event(), game.ongoing.SeesawTilting):
                break
        
        self.assertLess(i, maxticks)


        # after finishing, the seesaw should be tilted towards the landed ball. Left if chosen_column is even, right if odd
        expected_left = (chosen_column % 2 == 0)
        if expected_left:
            self.assertEqual(-1, game.playfield.get_seesaw_state(chosen_seesaw))
        else:
            self.assertEqual(1,  game.playfield.get_seesaw_state(chosen_seesaw))

    def test_throwing(self):
        game.reset()
        # drop a ball of weight 1 to the leftmost column. Wait until eventQueue is empty.
        ball1 = balls.ColoredBall(1, 1)
        game.playfield.land_ball_in_column(ball1, 0)
        while 0 != game.ongoing.get_number_of_events():
            game.tick()
        
        # Then a ball of weight 3 to the second-to-left. This should start a SeesawTilting 
        # and a ThrownBall, 2 to the right
        ball3 = balls.ColoredBall(1, 3)
        game.playfield.land_ball_in_column(ball3, 1)
        self.assertEqual(game.ongoing.get_number_of_events(), 2)
        the_throwing_event = game.ongoing.get_newest_event()
        self.assertIsInstance(the_throwing_event, game.ongoing.ThrownBall)
        self.assertEqual(the_throwing_event.getdestination(), 2)

        # Wait until the eventQueue is empty again
        while 0 != game.ongoing.get_number_of_events():
            game.tick()

        # Drop a ball of weight 15 to the left. This should throw the weight-3-ball to the left,
        # out-of-bounds. Total throwing range is 12 -> flying out twice,
        # ultimately landing in column 5, third from the right.

        ball15 = balls.ColoredBall(1, 15)
        game.playfield.land_ball_in_column(ball15, 0)
        the_throwing_event = game.ongoing.get_newest_event()
        self.assertIsInstance(the_throwing_event, game.ongoing.ThrownBall)
        self.assertIs(the_throwing_event.getball(), ball3)
        self.assertEqual(the_throwing_event.getdestination(), -1)

        # Pass Test if the newest event is ball3 falling in column 5. Fail Test if the eventQueue
        # is empty.
        while True:
            game.tick()
            self.assertNotEqual(0, game.ongoing.get_number_of_events())
            if isinstance(game.ongoing.get_newest_event(), game.ongoing.FallingBall):
                the_falling_event = game.ongoing.get_newest_event()
                self.assertIs(the_falling_event.getball(), ball3)
                self.assertEqual(the_falling_event.getcolumn(), 5)
                break

        # same test for (multiple) fly-outs to the right. Clear playfield and eventQueue first
        game.playfield.reset()
        game.ongoing.reset()

        Testball = balls.generate_ball()
        Testball.setweight(1)
        game.playfield.land_ball_in_column(Testball, 6)
        while 0 != game.ongoing.get_number_of_events():
            game.tick()
        Testball23 = balls.generate_ball()
        Testball23.setweight(23)
        game.playfield.land_ball_in_column(Testball23, 7)
        # range is 22. Two complete rotations are 16, remainder is 6. One to rightmost, 
        # five to go, land in column 4 since columns are zero-indexed
        while True:
            game.tick()
            self.assertNotEqual(0, game.ongoing.get_number_of_events())
            if isinstance(game.ongoing.get_newest_event(), game.ongoing.FallingBall):
                the_falling_event = game.ongoing.get_newest_event()
                self.assertIs(the_falling_event.getball(), Testball)
                self.assertEqual(the_falling_event.getcolumn(), 4)
                break

    def test_combining(self):
        game.reset()
        the_playfield = game.playfield

        # make solid ground: 50 weight to the leftmost column
        Testball = balls.generate_ball()
        Testball.setweight(50)
        Testball.setcolor(1)
        the_playfield.land_ball_in_column(Testball, 0)
        # wait until eventQueue is empty
        while 0 != game.ongoing.get_number_of_events():
            game.tick()
        
        # drop four balls, color=2, weights random, keep track of total weight
        totalweight = 0
        for i in range(4):
            nextball = balls.generate_starting_ball()
            nextball.setcolor(2)
            totalweight += nextball.getweight()
            the_playfield.land_ball_in_column(nextball, 0)
        # the eventQueue should be empty at this point
        self.assertEqual(0, game.ongoing.get_number_of_events())
        # the fifth ball should trigger the Combining
        triggerball = balls.generate_starting_ball()
        triggerball.setcolor(2)
        totalweight += triggerball.getweight()
        the_playfield.land_ball_in_column(triggerball, 0)

        # there should be a Combining now, at position (0,1). 
        self.assertGreater(game.ongoing.get_number_of_events(), 0)
        the_combining_event = game.ongoing.get_newest_event()
        self.assertIsInstance(the_combining_event, game.ongoing.Combining)
        self.assertEquals((0,1), the_combining_event.getposition())

        # After finishing eQ, check the resulting ball
        while 0 != game.ongoing.get_number_of_events():
            game.tick()
        
        resulting_ball = game.playfield.get_ball_at((0,1))
        self.assertIsInstance(resulting_ball, balls.ColoredBall)
        self.assertEqual(totalweight, resulting_ball.getweight())

if __name__ == '__main__':
    unittest.main()