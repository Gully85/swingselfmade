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

    def test_rightflyout_range(self):
        """create a ThrownBall that flies out. Verify that the remaining throwing-range is reduced correctly"""
        from ongoing import ThrownBall

        game.reset()

        the_ball: ColoredBall = generate_starting_ball()
        game.ongoing.throw_ball(the_ball, (6, 0), 2)
        the_throwing_event: ThrownBall = game.ongoing.get_event_of_type(ThrownBall)

        maxticks: int = 2 * int(constants.thrown_ball_totaltime * constants.max_FPS) + 1
        for _ in range(maxticks):
            game.tick()
            if the_throwing_event.getx() < 0.5:
                break
        else:
            # if this executes, the ball did not fly out
            self.assertFalse(True)

        self.assertEqual(the_throwing_event.getdestination(), 0)

    def test_flyout_conversions(self):
        """Throw a ColoredBall with high throwing range. It should convert to a Heart on the
        first fly-out, then Bomb, then Heart"""
        from ongoing import ThrownBall

        the_ball: ColoredBall = generate_starting_ball()
        game.ongoing.throw_ball(the_ball, (6, 0), 30)
        the_throwing_event: ThrownBall = game.ongoing.get_event_of_type(ThrownBall)

        # ticks per fly-through, not total
        maxticks: int = 2 * int(constants.thrown_ball_totaltime * constants.max_FPS) + 1
        for _ in range(maxticks):
            game.tick()
            if the_throwing_event.getx() < 0.5:
                break
        else:
            # if this executes, the ball did not fly out
            self.assertFalse(True)

        self.assertIsInstance(the_throwing_event.getball(), Heart)

        # There should be enough flying-range left to fly-out once more.
        self.assertGreater(the_throwing_event.remaining_range, 0)

        # Tick() until it reaches the half-way, then until x < 0.5 again. Check that both doesn't take too long
        for _ in range(maxticks):
            game.tick()
            if the_throwing_event.getx() > 4.0:
                break
        else:
            # if this executes, the ball did not reach the half-way mark
            self.assertFalse(True)

        for _ in range(maxticks):
            game.tick()
            if the_throwing_event.getx() < 0.5:
                break
        else:
            # if this executes, the ball did not fly-out a second time
            self.assertFalse(True)

        # Ball should convert to a Bomb at second fly-out
        self.assertIsInstance(the_throwing_event.getball(), Bomb)

        # Same once more, to verify that a Bomb converts to a Heart
        for _ in range(maxticks):
            game.tick()
            if the_throwing_event.getx() > 4.0:
                break
        else:
            # if this executes, the ball did not reach the half-way mark after 2nd fly-out
            self.assertFalse(True)

        for _ in range(maxticks):
            game.tick()
            if the_throwing_event.getx() < 0.5:
                break
        else:
            # if this executes, the ball did not fly-out the third time
            self.assertFalse(True)

        self.assertIsInstance(the_throwing_event.getball(), Heart)


class TestScoring(unittest.TestCase):

    # Helper function, no actual test
    def make_solid_ground(self):
        """Drop heavy (weight=50) balls, color=1, on one side of each seesaw. Wait for tilt to finish."""
        for sesa in range(4):
            column: int = 2 * sesa
            for _ in range(2):
                nextball: ColoredBall = generate_starting_ball()
                nextball.setcolor(1)
                nextball.setweight(50)
                nextball.lands_on_empty((column, 1))
                game.playfield.refresh_status()

        # wait for seesaws to stop tilting
        maxticks: int = int(1.0 / constants.tilting_per_tick) + 1
        self.assertTrue(wait_for_empty_eq(maxticks))

    def test_triplet_is_scored(self):
        """make solid ground, then land 3 same-colored ColoredBalls.
        Two must not score, the third must start a Scoring. Verify that
        it finishes and that it gives the correct amount of points."""
        from ongoing import Scoring

        game.reset()
        self.make_solid_ground()

        # drop two balls, color=2 in the three leftmost columns. Sum their weights.
        totalweight: int = 0
        for col in range(2):
            nextball: ColoredBall = generate_starting_ball()
            nextball.setcolor(2)
            totalweight += nextball.getweight()
            nextball.lands_on_empty((col, 3))
        game.playfield.refresh_status()

        self.assertFalse(game.ongoing.event_type_exists(Scoring))

        # drop third ball, this should start a Scoring
        nextball = generate_starting_ball()
        nextball.setcolor(2)
        totalweight += nextball.getweight()
        nextball.lands_on_empty((2, 3))
        game.playfield.refresh_status()

        game.tick()
        self.assertTrue(game.ongoing.event_type_exists(Scoring))

        # Scoring should finish within this many ticks
        maxticks: int = 4 * int(constants.max_FPS // constants.scoring_speed) + 1
        for _ in range(maxticks):
            game.tick()
            if not game.ongoing.event_type_exists(Scoring):
                break
        else:
            # if this is executed, Scoring did not finish in time
            self.assertTrue(False)

        self.assertEqual(game.getscore(), 3 * totalweight * game.getlevel())

    def test_scoring_extends_up_and_down(self):
        """Make solid ground. Then drop ColoredBalls to create a shape of Scoring that extends
        over multiple rows. Make sure it scores all connected balls."""
        from ongoing import Scoring

        game.reset()
        self.make_solid_ground()

        # Draw the following shape (numbers are colors, all weight 1):
        #
        # 2
        # 2 2
        # 2 3 3
        # then drop a color=2 ball to the third column. Verify that before that final ball, no
        # Scoring is started. Verify that the Scoring affects and removes five balls.

        ColoredBall(2, 1).lands_on_empty((0, 2))
        ColoredBall(3, 1).lands_on_empty((1, 2))
        ColoredBall(3, 1).lands_on_empty((2, 2))

        ColoredBall(2, 1).lands_on_empty((0, 3))
        ColoredBall(2, 1).lands_on_empty((1, 3))

        ColoredBall(2, 1).lands_on_empty((0, 4))

        self.assertFalse(game.ongoing.event_type_exists(Scoring))

        # Number of balls: 8 for the solid ground, 6 placed in this test.
        self.assertEqual(game.playfield.get_number_of_balls(), 14)

        ColoredBall(2, 1).lands_on_empty((2, 3))
        game.playfield.refresh_status()
        self.assertTrue(game.ongoing.event_type_exists(Scoring))

        # it should take 3 expansions for the Scoring to include all color=2 balls.
        maxticks: int = 5 * constants.scoring_delay + 1
        self.assertTrue(wait_for_empty_eq(maxticks))

        # There should be 10 balls left: 8 for the solid ground, 2 of the color=3
        self.assertEqual(game.playfield.get_number_of_balls(), 10)

    def test_scoring_drops_hanging_balls(self):
        """Tests that balls lieing on a Scored Ball will start to fall"""
        from ongoing import Scoring

        game.reset()
        self.make_solid_ground()

        # Draw the following shape (numbers are colors, weight is always 1):
        #   3
        # 2 2
        # then drop a 2 to the third column. Check that the color=3 ball is now a FallingBall and not in
        # the playfield any more.

        ColoredBall(2, 1).lands_on_empty((0, 2))
        ColoredBall(2, 1).lands_on_empty((1, 2))
        offcolor_ball = ColoredBall(3, 1)
        offcolor_ball.lands_on_empty((1, 3))

        self.assertFalse(game.ongoing.event_type_exists(Scoring))

        ColoredBall(2, 1).lands_on_empty((2, 2))
        game.playfield.refresh_status()
        self.assertTrue(game.ongoing.event_type_exists(Scoring))

        maxticks: int = 4 * constants.scoring_delay + 1
        for _ in range(maxticks):
            game.tick()
            if not game.ongoing.event_type_exists(Scoring):
                break
        else:
            # if this is executed, the Scoring did not finish in time
            self.assertFalse(True)

        self.assertTrue(game.ongoing.event_type_exists(FallingBall))
        falling_event: FallingBall = game.ongoing.get_event_of_type(FallingBall)
        self.assertEqual(offcolor_ball, falling_event.getball())
        self.assertEqual(falling_event.getcolumn(), 1)


class TestCombining(unittest.TestCase):

    # Helper function, no actual test
    def make_solid_ground(self):
        """Drop heavy (weight=50) balls, color=1, on one side of each seesaw. Wait for tilt to finish."""
        for sesa in range(4):
            column: int = 2 * sesa
            for _ in range(2):
                nextball: ColoredBall = generate_starting_ball()
                nextball.setcolor(1)
                nextball.setweight(50)
                nextball.lands_on_empty((column, 1))
                game.playfield.refresh_status()

        # wait for seesaws to stop tilting
        maxticks: int = int(1.0 / constants.tilting_per_tick) + 1
        self.assertTrue(wait_for_empty_eq(maxticks))

    def test_combining(self):
        """Stack 4 same-colored Balls, make sure they don't Combine. Land one more, make sure they do
        Combine and that the total weight is added."""
        from ongoing import Combining

        # Test deactivated for now, since there is no implementation for Combining
        return

        game.reset()
        self.make_solid_ground()

        # drop four balls, color=2, weights random, keep track of total weight
        totalweight: int = 0
        for i in range(4):
            nextball = generate_starting_ball()
            nextball.setcolor(2)
            totalweight += nextball.getweight()
            nextball.lands_on_empty((0, i + 2))
        # the eventQueue should be empty at this point
        self.assertEqual(0, game.ongoing.get_number_of_events())
        # the fifth ball should trigger the Combining
        triggerball = generate_starting_ball()
        triggerball.setcolor(2)
        totalweight += triggerball.getweight()
        triggerball.lands_on_empty((0, 6))
        game.playfield.refresh_status()

        # there should be a Combining now, at position (0,2).
        self.assertTrue(game.ongoing.event_type_exists(Combining))
        the_combining_event: Combining = game.ongoing.get_event_of_type(Combining)
        self.assertEqual((0, 2), the_combining_event.getposition())

        # After finishing eQ, check the resulting ball
        maxticks: int = constants.combining_totaltime
        self.assertTrue(wait_for_empty_eq(maxticks))

        resulting_ball = game.playfield.get_ball_at((0, 2))
        self.assertIsInstance(resulting_ball, ColoredBall)
        self.assertEqual(totalweight, resulting_ball.getweight())


class TestOngoing(unittest.TestCase):

    def make_solid_ground(self):
        """Drop heavy (weight=50) balls, color=1, on one side of each seesaw. Wait for tilt to finish."""
        for sesa in range(4):
            column: int = 2 * sesa
            for _ in range(2):
                nextball: ColoredBall = generate_starting_ball()
                nextball.setcolor(1)
                nextball.setweight(50)
                nextball.lands_on_empty((column, 1))
                game.playfield.refresh_status()

        # wait for seesaws to stop tilting
        maxticks: int = int(1.0 / constants.tilting_per_tick) + 1
        self.assertTrue(wait_for_empty_eq(maxticks))


if __name__ == "__main__":
    unittest.main()
