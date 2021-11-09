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
        game.playfield.land_ball((chosen_column, 1), Testball)
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

if __name__ == '__main__':
    unittest.main()