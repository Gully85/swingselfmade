# tests the ongoing module. Separate test_ method for each class in there

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

        # make sure it loses height over time
        self.assertIsInstance(the_falling_event, game.ongoing.FallingBall)
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
        game.playfield.land_ball(Testball, (chosen_column, 1))
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
        ball1 = balls.Colored_Ball(1, 1)
        game.playfield.land_ball(ball1, (0,1))
        while 0 != game.ongoing.get_number_of_events():
            game.tick()
        
        # Then a ball of weight 3 to the second-to-left. This should start a SeesawTilting 
        # and a ThrownBall, 2 to the right
        ball3 = balls.Colored_Ball(1, 3)
        game.playfield.land_ball(ball3, (1,2))
        self.assertEqual(game.ongoing.get_number_of_events(), 2)
        the_throwing_event = game.ongoing.get_newest_event()
        self.assertIsInstance(the_throwing_event, game.ongoing.ThrownBall)
        self.assertEqual(the_throwing_event.getdestination(), 2)

        # Wait until the eventQueue is empty again
        while 0 != game.ongoing.get_number_of_events():
            game.tick()

        # Drop a ball of weight 15 to the left. This should throw the weight-3-ball to the left,
        # out-of-bounds. Fly-out ranges should be -10, -2, 0. Finally, it should be converted to 
        # a FallingBall in the 2nd column from the right, index 6 (in the range 0..6)
        ball15 = balls.Colored_Ball(1, 15)
        game.playfield.land_ball(ball15, (0,2))
        the_throwing_event = game.ongoing.get_newest_event()
        self.assertIsInstance(the_throwing_event, game.ongoing.ThrownBall)
        self.assertIs(the_throwing_event.getball(), ball3)
        self.assertEqual(the_throwing_event.getdestination(), -1)

        # TODO enable these once the off-by-one in playfield.content is resolved
        if False:    
            self.assertEqual(the_throwing_event.getremaining_range(), -10)

            # wait until remaining_range changes
            while -10 == the_throwing_event.getremaining_range():
                game.tick()
            
            self.assertEqual(-1, the_throwing_event.getdestination())
            self.assertEqual(-2, the_throwing_event.getremaining_range())

            while -2 == the_throwing_event.getremaining_range():
                game.tick()

            self.assertEqual(0, the_throwing_event.getremaining_range())
            self.assertEqual(6, the_throwing_event.getdestination())



if __name__ == '__main__':
    unittest.main()