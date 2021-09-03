# provides Colorschemes. For now, a Colorscheme is just a list of Ballcolors and textcolors.
# For now, only 10 Colors are allowed. 
# taken from colorbrewer2.org, qualitative 10-class Set3. Ballcolors as set there, Textcolors all black

simple_standard_ballcolors = []

simple_standard_ballcolors.append((141,211,199))
simple_standard_ballcolors.append((255,255,179))
simple_standard_ballcolors.append((190,186,218))
simple_standard_ballcolors.append((251,128,114))
simple_standard_ballcolors.append((128,177,211))
simple_standard_ballcolors.append((253,180,98))
simple_standard_ballcolors.append((179,222,105))
simple_standard_ballcolors.append((252,205,229))
simple_standard_ballcolors.append((217,217,217))
simple_standard_ballcolors.append((188,128,189))

simple_standard_textcolors = []
for i in range(10):
	simple_standard_textcolors.append((0,0,0))

