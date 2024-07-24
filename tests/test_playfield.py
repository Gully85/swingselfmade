# tests the playfield module

import sys

sys.path.append("S:/SwingSelfmade/")

import game, constants

from balls import Ball, BlockedSpace, EmptySpace, ColoredBall
from balls import generate_starting_ball
from playfield import Playfield
from fallingball import FallingBall
from tests.testing_generals import wait_for_empty_eq
from constants import num_columns

import unittest


class TestPlayfield(unittest.TestCase):
    def test_playfield(self):
        game.reset()

        the_playfield: Playfield = game.playfield

        # at the beginning: The bottom row should be Blocked, the row
        # above that should be EmptySpace
        for i in range(num_columns):
            self.assertIsInstance(the_playfield.get_ball_at((i, 0)), BlockedSpace)
            self.assertIsInstance(the_playfield.get_ball_at((i, 1)), EmptySpace)

        # generate random ball, land it to the very left, wait until eventQueue is empty.
        # Seesaw must be tilted to the left, the ball must be at coords (0,0),
        # (1,0) and (1,1) must be Blocked
        Testball: ColoredBall = generate_starting_ball()
        the_playfield.land_ball_in_column(Testball, 0)
        maxticks: int = int(constants.max_FPS / constants.tilting_per_tick)
        self.assertTrue(wait_for_empty_eq(maxticks))
        self.assertEqual(the_playfield.get_seesaw_state(0), -1)
        self.assertIs(the_playfield.get_ball_at((0, 0)), Testball)
        self.assertIsInstance(the_playfield.get_ball_at((1, 0)), BlockedSpace)
        self.assertIsInstance(the_playfield.get_ball_at((1, 1)), BlockedSpace)

        # land a ball of equal weight in the neighboring column, wait for empty EventQueue,
        # should lead to balanced seesaws. Check that both balls are in the correct positions.
        Testball2: ColoredBall = generate_starting_ball()
        Testball2.setweight(Testball.getweight())
        the_playfield.land_ball_in_column(Testball2, 1)
        maxticks: int = int(constants.max_FPS // constants.tilting_per_tick)
        self.assertTrue(wait_for_empty_eq(maxticks))
        self.assertEqual(the_playfield.get_seesaw_state(0), 0)
        self.assertIs(the_playfield.get_ball_at((0, 1)), Testball)
        self.assertIs(the_playfield.get_ball_at((1, 1)), Testball2)

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
        Testball: ColoredBall = generate_starting_ball()
        Testball.setweight(20)
        the_playfield.land_ball_in_column(Testball, num_columns - 1)
        self.assertTrue(game.playfield.any_seesaw_is_moving())
        self.assertTrue(game.playfield.stacks[(num_columns // 2) - 1].ismoving())
        # the_tilting_event = game.ongoing.get_newest_event()
        # self.assertIsInstance(the_tilting_event, game.ongoing.SeesawTilting)
        # self.assertEqual(the_tilting_event.getsesa(), 3)

        # Scoring
        game.reset()
        # Drop two heavy balls on the left side of each seesaw to create a flat ground
        for sesa in range(num_columns // 2):
            Testball = generate_starting_ball()
            Testball.setweight(100)
            the_playfield.land_ball_in_column(Testball, 2 * sesa)
            Testball = generate_starting_ball()
            Testball.setweight(100)
            Testball.setcolor(1)
            the_playfield.land_ball_in_column(Testball, 2 * sesa)

        # wait for all tilts
        maxticks: int = constants.tilting_maxticks + 1
        for i in range(maxticks):
            game.tick()
            if not game.playfield.any_seesaw_is_moving():
                break
        else:
            self.fail("Tilt did not finish within expected time")

        # put equal-colored balls in the three leftmost columns. This should start a Scoring.
        for i in range(3):
            Testball2 = generate_starting_ball()
            Testball2.setcolor(2)
            the_playfield.land_ball_in_column(Testball2, i)
        the_playfield.refresh_status()
        game.tick()
        self.assertIsInstance(game.ongoing.get_newest_event(), game.ongoing.Scoring)
        self.assertTrue(wait_for_empty_eventQueue(4 * constants.scoring_delay))

        # same for the rightmost columns and a different color
        for i in range(num_columns - 3, num_columns):
            Testball3 = generate_starting_ball()
            Testball3.setcolor(3)
            the_playfield.land_ball_in_column(Testball3, i)
        game.tick()
        self.assertIsInstance(game.ongoing.get_newest_event(), game.ongoing.Scoring)
        self.assertTrue(wait_for_empty_eventQueue(4 * constants.scoring_delay))

        # Combining. Skipped for now. TODO
        if False:
            # land 5 equal balls in column 4, they should combine
            for i in range(5):
                Testball4 = balls.generate_starting_ball()
                Testball4.setcolor(2)
                Testball4.setweight(3)
                the_playfield.land_ball_in_column(Testball4, 4)
            game.tick()
            self.assertIsInstance(
                game.ongoing.get_newest_event(), game.ongoing.Combining
            )
            self.assertTrue(
                wait_for_empty_eventQueue(
                    constants.combining_totaltime * constants.max_FPS
                )
            )
            # The resulting ball should be at position (4,2), color=2, weight=15
            resulting_ball = the_playfield.get_ball_at((4, 2))
            self.assertIsInstance(resulting_ball, balls.ColoredBall)
            self.assertEqual(resulting_ball.getcolor(), 2)
            self.assertEqual(resulting_ball.getweight(), 15)

        # Hanging Balls
        game.reset()
        # drop two balls in column 6, remove the lower one, assert that the higher one starts to fall
        Testball = generate_starting_ball()
        the_playfield.land_ball_in_column(Testball, 6)
        Testball2 = generate_starting_ball()
        the_playfield.land_ball_in_column(Testball2, 6)
        # wait until tilting is finished
        maxticks: int = constants.tilting_maxticks
        for _ in range(maxticks):
            pass
            game.tick()
            if not game.playfield.any_seesaw_is_moving():
                break
        else:
            self.fail("Tilting did not finish within expected time")

        # remove lower one and trigger a status update
        the_playfield.remove_ball_at((6, 0))
        the_playfield.refresh_status()
        game.tick()

        # both positions should be empty now, newest Event should be FallingBall Testball2
        self.assertIsInstance(the_playfield.get_ball_at((6, 0)), EmptySpace)
        self.assertIsInstance(the_playfield.get_ball_at((6, 1)), EmptySpace)
        self.assertTrue(game.ongoing.event_type_exists(FallingBall))
        the_falling_event: FallingBall = game.ongoing.get_event_of_type(FallingBall)
        self.assertEqual(the_falling_event.getcolumn(), 6)
        self.assertIs(the_falling_event.getball(), Testball2)


def wait_for_empty_eventQueue(maxticks: int):
    """Waits until the eventQueue is empty, up to specified number of ticks. Returns True
    if the eventQueue got empty."""
    maxticks = int(maxticks + 1.0)
    for i in range(maxticks):
        game.tick()
        if 0 == game.ongoing.get_number_of_events():
            return True
    return False


if __name__ == "__main__":
    unittest.main()
