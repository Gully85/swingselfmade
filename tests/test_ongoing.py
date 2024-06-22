# tests the ongoing module. Separate test_ method for each class in there

import sys

sys.path.append("S:/SwingSelfmade/")

import game, constants
from balls import Ball, ColoredBall, Heart, Bomb
from balls import generate_starting_ball
from ongoing import FallingBall
import unittest, random

from tests.testing_generals import wait_for_empty_eq


class TestFalling(unittest.TestCase):
    def test_dropping(self):
        """create a random ball, drop it in a random column. Assert it is inserted into EventQueue"""
        game.reset()

        Testball: Ball = generate_starting_ball()
        chosen_column: int = random.randint(0, 7)
        game.ongoing.drop_ball_in_column(Testball, chosen_column)

        self.assertEqual(1, game.ongoing.get_number_of_events())
        the_falling_event: FallingBall = game.ongoing.get_newest_event()
        self.assertIsInstance(the_falling_event, game.ongoing.FallingBall)
        self.assertEqual(the_falling_event.getcolumn(), chosen_column)

    def test_falling(self):
        """create a random ball, drop it in a random column. Assert that it loses height."""
        game.reset()

        game.ongoing.drop_ball_in_column(generate_starting_ball(), random.randint(0, 7))
        the_falling_event: FallingBall = game.ongoing.get_newest_event()

        # make sure it loses height over time
        starting_height: float = the_falling_event.getheight()
        game.tick()
        self.assertLess(the_falling_event.getheight(), starting_height)

    def test_fallingball_reaches_ground(self):
        """create a random ball, drop it in a random column. Assert that it reaches the ground eventually"""
        game.reset()

        game.ongoing.drop_ball_in_column(generate_starting_ball(), random.randint(0, 7))

        # it should land after some time. Maximum number of ticks allowed is 8.0 / falling_speed * max_FPS
        # (it should only need to drop by 7 positions and then trigger a Seesaw Tilting, 8.0 leaves some room)
        maxticks = int(8.0 * constants.max_FPS / constants.falling_per_tick) + 1
        self.assertGreater(maxticks, 0)
        self.assertTrue(wait_for_empty_eq(maxticks))
        self.assertFalse(game.ongoing.event_type_exists(FallingBall))


class TestTilting(unittest.TestCase):
    def test_tilting(self):
        """create a Ball, land it, assert that the seesaw's tilt changes per tick.
        And assert that the sum of the heights stays roughly 0.0"""
        game.reset()

        Testball: ColoredBall = generate_starting_ball()

        chosen_column: int = random.randint(0, 7)
        chosen_seesaw: int = chosen_column // 2
        Testball.lands_on_empty((chosen_column, 1))
        game.playfield.refresh_status()

        the_sesa = game.playfield.stacks[chosen_seesaw]
        self.assertTrue(the_sesa.ismoving())

        initial_tiltvalue: float = the_sesa.gettilt()
        game.tick()
        self.assertNotEqual(initial_tiltvalue, the_sesa.gettilt())

    def test_tilting_up_equals_down(self):
        """Drop a ball to one side of the seesaw. Assert that during tilt, the sum of the landing-heights
        stays constant."""
        chosen_col: int = 0
        generate_starting_ball().lands_on_empty((chosen_col, 1))

        ticks_for_full_tilt: int = int(1.0 / constants.tilting_per_tick)
        for _ in range(ticks_for_full_tilt):
            game.tick()
            self.assertAlmostEqual(
                game.playfield.stacks[0].get_blocked_height(left=True)
                + game.playfield.stacks[0].get_blocked_height(left=False),
                2.0,
            )

        chosen_col: int = 7
        generate_starting_ball().lands_on_empty((chosen_col, 2))

        for _ in range(ticks_for_full_tilt):
            game.tick()
            self.assertAlmostEqual(
                game.playfield.stacks[chosen_col // 2].get_blocked_height(left=True)
                + game.playfield.stacks[chosen_col // 2].get_blocked_height(left=False),
                2.0,
            )

    # TODO atm there is no SeesawTilting event type. Insert test here once that exists.

    def test_tilting_finishes(self):
        """land generated Ball with non-zero weight on random column. Assert that it eventually stops moving."""
        game.reset()

        Testball: ColoredBall = generate_starting_ball()
        self.assertNotEqual(0, Testball.getweight())

        chosen_column: int = random.randint(0, 7)
        chosen_sesa: int = chosen_column // 2

        Testball.lands_on_empty((chosen_column, 2))
        game.playfield.refresh_status()
        self.assertTrue(game.playfield.stacks[chosen_sesa].ismoving())

        maxticks: int = int(1.0 / constants.tilting_per_tick) + 1
        self.assertTrue(wait_for_empty_eq(maxticks))

        self.assertFalse(game.playfield.stacks[chosen_sesa].ismoving())

    def test_tilting_ends_towards_heavier_side(self):
        """generate random Ball and land it somewhere, wait for tilting to finish. Once on the left side, once on the right side.
        Verify that the tilt ends towards the Ball."""
        game.reset()

        chosen_column: int = 0
        generate_starting_ball().lands_on_empty((chosen_column, 2))
        game.playfield.refresh_status()
        # wait for tilt to finish
        maxticks: int = int(1.0 / constants.tilting_per_tick) + 1
        self.assertTrue(wait_for_empty_eq(maxticks))

        self.assertEqual(-1, game.playfield.get_seesaw_state(chosen_column))
        self.assertEqual(1, game.playfield.get_seesaw_state(chosen_column + 1))

        # test on the rightmost column, should tilt to the right
        chosen_column: int = 7
        generate_starting_ball().lands_on_empty((chosen_column, 2))
        game.playfield.refresh_status()
        maxticks: int = int(1.0 / constants.tilting_per_tick) + 1
        self.assertTrue(wait_for_empty_eq(maxticks))

        self.assertEqual(1, game.playfield.get_seesaw_state(chosen_column - 1))
        self.assertEqual(-1, game.playfield.get_seesaw_state(chosen_column))


class TestThrowing(unittest.TestCase):

    def test_throwing_range(self):
        """land a Ball with weight 1 in column 0, then a Ball with weight 3 in column 1.
        Assert that the first Ball is thrown with range 2."""
        game.reset()

        ball1: ColoredBall = ColoredBall(1, 1)
        ball1.lands_on_empty((0, 1))
        game.playfield.refresh_status()
        maxticks: int = int(1.0 / constants.tilting_per_tick) + 1
        self.assertTrue(wait_for_empty_eq(maxticks))

        ball2: ColoredBall = ColoredBall(1, 3)
        ball2.lands_on_empty((1, 2))
        game.playfield.refresh_status()

        self.assertTrue(game.ongoing.event_type_exists(game.ongoing.ThrownBall))
        the_throwing_event = game.ongoing.get_event_of_type(game.ongoing.ThrownBall)
        self.assertEqual(the_throwing_event.getball(), ball1)
        self.assertEqual(the_throwing_event.getdestination(), 2)

    def test_thrown_ball_falls(self):
        """create a ThrownBall, assert that it converts to a FallingBall eventually"""
        from ongoing import ThrownBall

        game.reset()
        the_ball: ColoredBall = generate_starting_ball()
        game.ongoing.throw_ball(the_ball, (0, 0), 2)

        maxticks: int = int(constants.thrown_ball_totaltime * constants.max_FPS) + 1
        for _ in range(maxticks):
            game.tick()
            if game.ongoing.event_type_exists(game.ongoing.FallingBall):
                break
        else:
            # if this executes, the ThrownBall was not converted into a FallingBall
            self.assertFalse(True)

        the_falling_event = game.ongoing.get_event_of_type(game.ongoing.FallingBall)
        self.assertIsInstance(the_falling_event, FallingBall)
        self.assertEqual(the_ball, the_falling_event.getball())
        self.assertEqual(2, the_falling_event.getcolumn())

    def test_leftflyout_range(self):
        """create a ThrownBall that flies out. Verify that the remaining throwing-range is reduced correctly"""
        from ongoing import ThrownBall

        game.reset()

        the_ball: ColoredBall = generate_starting_ball()
        game.ongoing.throw_ball(the_ball, (1, 0), -2)
        the_throwing_event: ThrownBall = game.ongoing.get_event_of_type(ThrownBall)

        maxticks: int = 2 * int(constants.thrown_ball_totaltime * constants.max_FPS) + 1
        for _ in range(maxticks):
            game.tick()
            if the_throwing_event.getx() > 6.5:
                break
        else:
            # if this executes, the ball did not fly out
            self.assertFalse(True)

        self.assertEqual(the_throwing_event.getdestination(), 7)


class TestOngoing(unittest.TestCase):

    def test_throwing(self):
        game.reset()

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

        ball15 = ColoredBall(1, 15)
        ball15.lands_on_empty((0, 2))
        game.playfield.refresh_status()
        self.assertTrue(game.ongoing.event_type_exists(game.ongoing.ThrownBall))
        the_throwing_event = game.ongoing.get_event_of_type(game.ongoing.ThrownBall)
        # self.assertIs(the_throwing_event.getball(), ball3)
        self.assertEqual(
            the_throwing_event.getdestination(), -1
        )  # destination -1 indicates fly-out
        # to the left

        # eventually, the ThrowingBall event should convert into a FallingBall event
        # (Bomb in column 5).
        maxticks = 100000
        for i in range(maxticks - 1):
            game.tick()
            if not game.ongoing.event_type_exists(game.ongoing.ThrownBall):
                break
        self.assertLess(i, maxticks)

        self.assertTrue(game.ongoing.event_type_exists(game.ongoing.FallingBall))
        the_falling_event = game.ongoing.get_event_of_type(game.ongoing.FallingBall)
        self.assertIsInstance(the_falling_event.getball(), Bomb)
        self.assertEqual(the_falling_event.getcolumn(), 5)

        # same test for (multiple) fly-outs to the right. Clear playfield and eventQueue first
        game.playfield.reset()
        game.ongoing.reset()

        Testball = generate_starting_ball()
        Testball.setweight(1)
        Testball.lands_on_empty((6, 1))
        game.playfield.refresh_status()
        while game.playfield.any_seesaw_is_moving():
            game.tick()

        Testball23 = generate_starting_ball()
        Testball23.setweight(23)
        Testball23.lands_on_empty((7, 2))
        game.playfield.refresh_status()
        # range is 22. Two complete rotations are 16, remainder is 6. One to rightmost,
        # five to go, land in column 4 since columns are zero-indexed. Should convert into
        # a Heart (3 fly-outs)

        for i in range(maxticks - 1):
            game.tick()
            if not game.ongoing.event_type_exists(game.ongoing.ThrownBall):
                break
        self.assertLess(i, maxticks)
        self.assertTrue(game.ongoing.event_type_exists(game.ongoing.FallingBall))
        the_falling_event = game.ongoing.get_event_of_type(game.ongoing.FallingBall)
        self.assertIsInstance(the_falling_event.getball(), Heart)
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
        self.assertEqual((0, 1), the_combining_event.getposition())

        # After finishing eQ, check the resulting ball
        while 0 != game.ongoing.get_number_of_events():
            game.tick()

        resulting_ball = game.playfield.get_ball_at((0, 1))
        self.assertIsInstance(resulting_ball, balls.ColoredBall)
        self.assertEqual(totalweight, resulting_ball.getweight())

    def test_scoring(self):
        game.reset()
        the_playfield = game.playfield

        # make solid ground: 2x 50 weight, color=1 to every left-side of a seesaw
        for sesa in range(4):
            column = 2 * sesa
            for _ in range(2):
                nextball = generate_starting_ball()
                nextball.setcolor(1)
                nextball.setweight(50)
                nextball.lands_on_empty(
                    (column, 1)
                )  # y-value is ignored on ColoredBalls
            the_playfield.refresh_status()

        maxticks = int(1e6)
        self.assertTrue(wait_for_empty_eq(maxticks))

        self.assertEqual(the_playfield.get_seesaw_state(column), -1)

        # drop ball colors like this:
        #
        # 2 3
        # 3 3 3
        # all the 3's should score (keep track of total weight), the 2 should become a FallingBall
        nextball = generate_starting_ball()
        nextball.setcolor(3)
        total_weight = nextball.getweight()
        nextball.lands_on_empty((0, 2))
        the_playfield.refresh_status()

        other_colored_ball = generate_starting_ball()
        other_colored_ball.setcolor(2)
        other_colored_ball.lands_on_empty((0, 3))
        the_playfield.refresh_status()

        for _ in range(2):
            nextball = generate_starting_ball()
            nextball.setcolor(3)
            total_weight += nextball.getweight()
            nextball.lands_on_empty((1, 4))
        the_playfield.refresh_status()

        self.assertEqual(0, game.getscore())
        self.assertEqual(4, game.getlevel())

        # this ball should start the scoring
        nextball = generate_starting_ball()
        nextball.setcolor(3)
        total_weight += nextball.getweight()
        nextball.lands_on_empty((2, 4))
        the_playfield.refresh_status()

        game.tick()

        self.assertTrue(game.ongoing.event_type_exists(game.ongoing.Scoring))

        # after some ticks, the other_colored_ball should start dropping
        maxticks = int(1e6)
        self.assertTrue(wait_for_empty_eq(maxticks))

        # check correct position of dropped ball
        the_landed_ball = game.playfield.get_ball_at((0, 2))
        self.assertIs(the_landed_ball, other_colored_ball)
        self.assertEqual(game.getscore(), 16 * total_weight)

        # there should be the 8 weight-50 balls that create a solid ground,
        # and the other_colored_ball. Make sure no other balls are there.
        self.assertEqual(the_playfield.get_number_of_balls(), 9)


if __name__ == "__main__":
    unittest.main()
