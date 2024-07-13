# provides Colorschemes. For now, a Colorscheme is just a list of Ballcolors and textcolors.
# For now, only 10 Colors are allowed.
# taken from colorbrewer2.org, qualitative 10-class Set3. Ballcolors as set there, Textcolors all black


from typing import Tuple, List


simple_standard_ball_colors: List[Tuple[int, int, int]] = [
    (141, 211, 199),
    (255, 255, 179),
    (190, 186, 218),
    (251, 128, 114),
    (128, 177, 211),
    (253, 180, 98),
    (179, 222, 105),
    (252, 205, 229),
    (217, 217, 217),
    (188, 128, 189),
]

simple_standard_text_colors: List[Tuple[int, int, int]] = []
for i in range(10):
    simple_standard_text_colors.append((0, 0, 0))


RGB_black: Tuple[int, int, int] = (0, 0, 0)

RGB_lightgrey: Tuple[int, int, int] = (217, 217, 217)

RGB_red: Tuple[int, int, int] = (255, 0, 0)

RGB_scoringcolor: Tuple[int, int, int] = (65, 174, 118)
