# contains some code used several times in tests.

import sys
sys.path.append("S:/SwingSelfmade/")


import game, ongoing


def wait_for_empty_eq(maxticks: int):
    """performs tick()s until nothing is happening any more.
    Parameter is the maximum number of ticks. Return False if 
    after that many ticks, something is still going on"""
    for i in range(maxticks-1):
        game.tick()
        if (ongoing.get_number_of_events() == 0 and
           not game.playfield.any_seesaw_is_moving()):
           return True
    
    return False