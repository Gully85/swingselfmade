# Class file to hold the Scoring class

from typing import List, Tuple

from balls import Ball

from ongoing import Ongoing, remove_from_EQ


class Scoring(Ongoing):
    """Balls currently scoring points. Expands every few ticks to connected
    Balls of the same color, when finished all the Balls are removed.
    Constructor: Scoring((x,y), ball)
    """

    past: List[Ball]
    next: List[Tuple[int]]
    delay: int
    weight_so_far: int
    ball: Ball  # used in expansion to check if the color matches

    def __init__(self, coords: Tuple[int, int], ball: Ball):
        from constants import scoring_delay

        self.past = []  # list of ScoringColoredBalls
        self.next = [coords]  # list of (int,int) coords in the playfield
        self.delay = scoring_delay
        self.weight_so_far = 0
        self.ball = ball  # this is used to match colors when deciding
        # whether to expand. Should be a ColoredBall or Heart

    @staticmethod
    def start_score(coords) -> None:
        import game
        from ongoing import add_to_EQ

        first_ball: Ball = game.playfield.get_ball_at(coords)
        add_to_EQ(Scoring(coords, first_ball))

    def draw(self, surf) -> None:
        # placeholder: Rectangles. Green (65,174,118) for past and slightly
        # brighter green (102,194,164) for next
        pass
        # nextcolor = (102,194,164)
        # for(x,y) in self.next:
        #    xcoord, ycoord = pixel_coord_in_playfield((x,y))
        #    pygame.draw.rect(surf, nextcolor, pygame.Rect((xcoord,ycoord), ball_size), width=3)

    def tick(self) -> None:
        """called once per tick. Counts down delay, expands if zero was reached, and reset delay.
        If no expansion, removes this from the eventQueue
        """

        import game
        from constants import scoring_delay
        from balls import ColoredBall, Heart

        self.delay -= 1
        if self.delay > 0:
            return

        if self.expand():
            self.delay = scoring_delay
            return

        if isinstance(self.ball, ColoredBall):
            # Formula for Scores: Total weight x number of balls x level
            score_from_this = (
                self.weight_so_far * len(self.past) * game.level * game.getscorefactor()
            )
            game.addscore(score_from_this)
        elif isinstance(self.ball, Heart):
            game.increase_score_factor(len(self.past))

        game.playfield.finalize_scoring(self.past)
        remove_from_EQ(self)
        game.playfield.refresh_status()

    def expand(self) -> None:
        """checks if neighboring balls are same color, removes them and saves their coords in
        self.next for the next expand() call. Returns True if the Scoring grew.
        """
        from balls import PlayfieldSpace
        from constants import num_columns, max_height
        import game

        now: List[Tuple[int, int]] = self.next
        self.next = []
        for coords in now:
            new_ball: PlayfieldSpace = game.playfield.get_ball_at(coords)
            # do not expand to a position that already has a scoring Ball,
            # and not to a position that does not match colors
            if new_ball.is_scoring() or not new_ball.matches_color(self.ball):
                continue

            new_ball.mark_for_scoring()
            self.weight_so_far += new_ball.getweight()
            self.past.append(new_ball)

            x, y = coords
            coords_to_check: List[Tuple[int, int]] = [
                (x - 1, y),
                (x + 1, y),
                (x, y - 1),
                (x, y + 1),
            ]
            # remove out-of-bounds from this list
            for x2, y2 in coords_to_check:
                if x2 < 0 or x2 > num_columns - 1 or y2 < 0 or y2 > max_height:
                    continue
                self.next.append((x2, y2))

        # print("more matching Balls found: next=",self.next)
        return len(self.next) > 0
