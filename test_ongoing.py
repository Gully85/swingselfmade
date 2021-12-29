# tests the ongoing module. Separate test_ method for each class in there

import game, balls, constants
import unittest, random

from testing_generals import wait_for_empty_eq


class TestOngoing(unittest.TestCase):
    def test_falling(self):
        game.reset()

        # create a random ball, drop it in a random column
        Testball = balls.generate_starting_ball()
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
        # (it should only need to drop by 7 positions and then trigger a Seesaw Tilting, 8.0 leaves some room)
        maxticks = int(8.0 * constants.max_FPS / constants.falling_per_tick)
        self.assertGreater(maxticks, 0)
        self.assertTrue(wait_for_empty_eq(maxticks))
        
        # The seesaw where it landed, should now be in a not-balanced position
        self.assertNotEqual(0, game.playfield.get_seesaw_state(chosen_column))
        
    def test_tilting(self):
        game.reset()

        # create a ball, land it
        Testball = balls.generate_starting_ball()
        chosen_column = random.randint(0,7)
        chosen_seesaw = chosen_column//2
        Testball.lands_on_empty((chosen_column,1))
        game.playfield.refresh_status()
        the_sesa = game.playfield.stacks[chosen_seesaw]
        self.assertTrue(the_sesa.ismoving())

        # make sure tilt changes per tick
        initial_progress = the_sesa.gettilt()
        game.tick()
        self.assertNotEqual(the_sesa.gettilt(), initial_progress)

        # it should finish after some time. Expected number of ticks is (1. / tilting_per_tick)
        maxticks = int(1./ constants.tilting_per_tick) + 1
        self.assertTrue(wait_for_empty_eq(maxticks))


        # after finishing, the seesaw should be tilted towards the landed ball. 
        # exact column always down (-1), connected_neighbor up (+1)
        # Landed left if chosen_column is even, right if odd
        self.assertEqual(-1, game.playfield.get_seesaw_state(chosen_column))
        landed_left = (chosen_column % 2 == 0)
        if landed_left:
            neighbor_column = chosen_column + 1
        else:
            neighbor_column = chosen_column - 1
        self.assertEqual(1, game.playfield.get_seesaw_state(neighbor_column))

    def test_throwing(self):
        game.reset()
        # drop a ball of weight 1 to the leftmost column. Wait until tilting is finished.
        ball1 = balls.ColoredBall(1, 1)
        
        ball1.lands_on_empty((0,1))
        game.playfield.refresh_status()
        maxticks = int(2.*constants.max_FPS/constants.tilting_per_tick + 1)
        self.assertTrue(wait_for_empty_eq(maxticks))
        
        # Then a ball of weight 3 to the second-to-left. This should start a 
        # ThrownBall, range 2 to the right. Should land in column 2.
        ball3 = balls.ColoredBall(1, 3)
        ball3.lands_on_empty((1,2))
        game.playfield.refresh_status()
        self.assertTrue(game.ongoing.event_type_exists(game.ongoing.ThrownBall))
        the_throwing_event = game.ongoing.get_event_of_type(game.ongoing.ThrownBall)
        self.assertEqual(the_throwing_event.getdestination(), 2)

        # Wait until it flew over to that column
        while game.ongoing.event_type_exists(game.ongoing.ThrownBall):
            game.tick()
        # it should now fall
        self.assertTrue(game.ongoing.event_type_exists(game.ongoing.FallingBall))
        the_falling_event = game.ongoing.get_event_of_type(game.ongoing.FallingBall)
        self.assertEqual(the_falling_event.getcolumn(), 2)

        # Drop a ball of weight 15 to the left. This should throw the weight-3-ball to the left,
        # out-of-bounds. Total throwing range is 12 -> flying out twice,
        # ultimately landing in column 5, third from the right. Should convert into a Bomb (2 fly-outs)

        ball15 = balls.ColoredBall(1, 15)
        ball15.lands_on_empty((0,2))
        game.playfield.refresh_status()
        self.assertTrue(game.ongoing.event_type_exists(game.ongoing.ThrownBall))
        the_throwing_event = game.ongoing.get_event_of_type(game.ongoing.ThrownBall)
        self.assertIs(the_throwing_event.getball(), ball3)
        self.assertEqual(the_throwing_event.getdestination(), -1)   # destination -1 indicates fly-out
                                                                    # to the left

        # eventually, the ThrowingBall event should convert into a FallingBall event
        # (Bomb in column 5).
        maxticks = 100000
        for i in range(maxticks-1):
            game.tick()
            if not game.ongoing.event_type_exists(game.ongoing.ThrownBall):
                break
        self.assertLess(i, maxticks)

        self.assertTrue(game.ongoing.event_type_exists(game.ongoing.FallingBall))
        the_falling_event = game.ongoing.get_event_of_type(game.ongoing.FallingBall)
        self.assertIsInstance(the_falling_event.getball(), balls.Bomb)
        self.assertEqual(the_falling_event.getcolumn(), 5)


        # same test for (multiple) fly-outs to the right. Clear playfield and eventQueue first
        game.playfield.reset()
        game.ongoing.reset()

        Testball = balls.generate_starting_ball()
        Testball.setweight(1)
        Testball.lands_on_empty((6,1))
        game.playfield.refresh_status()
        while game.playfield.any_seesaw_is_moving():
            game.tick()
        
        Testball23 = balls.generate_starting_ball()
        Testball23.setweight(23)
        Testball23.lands_on_empty((7,2))
        game.playfield.refresh_status()
        # range is 22. Two complete rotations are 16, remainder is 6. One to rightmost, 
        # five to go, land in column 4 since columns are zero-indexed. Should convert into
        # a Heart (3 fly-outs)

        for i in range(maxticks-1):
            game.tick()
            if not game.ongoing.event_type_exists(game.ongoing.ThrownBall):
                break
        self.assertLess(i, maxticks)
        self.assertTrue(game.ongoing.event_type_exists(game.ongoing.FallingBall))
        the_falling_event = game.ongoing.get_event_of_type(game.ongoing.FallingBall)
        self.assertIsInstance(the_falling_event.getball(), balls.Heart)
        self.assertEqual(the_falling_event.getcolumn(), 4)

    def test_combining(self):
        return
        game.reset()
        the_playfield = game.playfield

        # make solid ground: 50 weight to the leftmost column
        Testball = balls.generate_starting_ball()
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
        self.assertEqual((0,1), the_combining_event.getposition())

        # After finishing eQ, check the resulting ball
        while 0 != game.ongoing.get_number_of_events():
            game.tick()
        
        resulting_ball = game.playfield.get_ball_at((0,1))
        self.assertIsInstance(resulting_ball, balls.ColoredBall)
        self.assertEqual(totalweight, resulting_ball.getweight())

    def test_scoring(self):
        game.reset()
        the_playfield = game.playfield

        # make solid ground: 2x 50 weight, color=1 to every left-side of a seesaw
        for sesa in range(4):
            column = 2*sesa
            for _ in range(2):
                nextball = balls.generate_starting_ball()
                nextball.setcolor(1)
                nextball.setweight(50)
                nextball.lands_on_empty((column, 1)) # y-value is ignored on ColoredBalls
            the_playfield.refresh_status()
        
        maxticks = int(1e6)
        self.assertTrue(wait_for_empty_eq(maxticks))
        
        self.assertEqual(the_playfield.get_seesaw_state(column), -1)
    
        # drop ball colors like this:
        #
        # 2 3
        # 3 3 3
        # all the 3's should score (keep track of total weight), the 2 should become a FallingBall
        nextball = balls.generate_starting_ball()
        nextball.setcolor(3)
        total_weight = nextball.getweight()
        nextball.lands_on_empty((0,2))
        the_playfield.refresh_status()

        other_colored_ball = balls.generate_starting_ball()
        other_colored_ball.setcolor(2)
        other_colored_ball.lands_on_empty((0,3))
        the_playfield.refresh_status()

        for _ in range(2):
            nextball = balls.generate_starting_ball()
            nextball.setcolor(3)
            total_weight += nextball.getweight()
            nextball.lands_on_empty((1,4))
        the_playfield.refresh_status()
        
        self.assertEqual(0, game.getscore())
        self.assertEqual(4, game.getlevel())
        
        # this ball should start the scoring
        nextball = balls.generate_starting_ball()
        nextball.setcolor(3)
        total_weight += nextball.getweight()
        nextball.lands_on_empty((2,4))
        the_playfield.refresh_status()
        
        game.tick()
        
        self.assertTrue(game.ongoing.event_type_exists(game.ongoing.Scoring))

        # after some ticks, the other_colored_ball should start dropping
        maxticks = int(1e6)
        self.assertTrue(wait_for_empty_eq(maxticks))

        # check correct position of dropped ball        
        the_landed_ball = game.playfield.get_ball_at((0,2))
        self.assertIs(the_landed_ball, other_colored_ball)
        self.assertEqual(game.getscore(), 16*total_weight)
        
        # there should be the 8 weight-50 balls that create a solid ground,
        # and the other_colored_ball. Make sure no other balls are there.
        self.assertEqual(the_playfield.get_number_of_balls(), 9)
        


if __name__ == '__main__':
    unittest.main()