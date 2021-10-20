# swingselfmade
An attempt to re-implement a 90s PC game

To run: Copy all the .py files, install Python and the pygame module, run python SelfSwing_main.py

This is an (atm incomplete and buggy) re-implementation of the 90s PC game Swing. The archetype is like Tetris, drop things
that disappear for points if you align them well, and if everything is filled you lose. The objects are Balls with a color and weight, 
the playfield is made of 4 seesaws that tilt towards the heavier side. If a seesaw flips over, the top ball of the lighter side
is thrown sideways for as many columns as the weight-difference. A horizontal line of three Balls of the same color will score all 
connected Balls of the same color, score added is (number of balls) x (total weight) x (level). The level is the number of different
colors that spawn, increases every 50 balls dropped.

A list of what will probably be added soon is in NOTES.txt. 