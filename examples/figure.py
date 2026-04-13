#!/usr/bin/env python

"""figure.py - An example of figure construction.

Copyright (C) 2008 David Boddie <david@boddie.org.uk>

This file is part of the ldraw Python package.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from py4bricks.figure import *
from py4bricks.library.colours import *
from py4bricks.library.parts.minifig.accessories import HairMale
from py4bricks.library.parts.minifig.torsos import Torso

figure = Person()
print(figure.head(colour=Yellow, angle=35))
print(figure.hat(colour=Black, part=HairMale))  # Hair Male
print(figure.torso(colour=Red, part=Torso))  # Torso
print(figure.hips(colour=Blue))
print(figure.left_leg(colour=Blue, angle=5))
print(figure.right_leg(colour=Blue, angle=20))
print(figure.left_arm(colour=Red, angle=0))
print(figure.left_hand(colour=Yellow, angle=0))
print(figure.right_arm(colour=Red, angle=-90))
print(figure.right_hand(colour=Yellow, angle=0))
print()
print(Piece(colour=White, position=Vector(150, -100, -150), rotation=Identity(), part="LIGHT"))
print(Piece(colour=White, position=Vector(-150, -100, -150), rotation=Identity(), part="LIGHT"))
print(Piece(colour=White, position=Vector(0, -100, 150), rotation=Identity(), part="LIGHT"))

# Camera should be at 120.0,-20.0,-140.0 in LDraw coordinates.
