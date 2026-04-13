#!/usr/bin/env python

"""diver.py - An example of figure construction.

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
from py4bricks.library.parts.minifig.accessories import (
    Airtanks,
    CameraMovie,
    HelmetVisorDiverMask,
    FlipperThin,
    HairMale,
)
from py4bricks.library.parts.minifig.torsos import Torso
from py4bricks.pieces import Piece

figure = Person(position=Vector(0, 0, -10), rotation=Identity().rotate(-15, ZAxis).rotate(20, XAxis))
print(figure.head(Yellow, -15))
print(figure.hat(colour=Black, part=HelmetVisorDiverMask))
print(figure.hat(colour=Black, part=HairMale))
print(figure.torso(colour=Yellow, part=Torso))
print(figure.backpack(colour=Black, displacement=Vector(0, -2, 0), part=Airtanks))
print(figure.hips(colour=Green))
print(figure.left_leg(colour=Yellow, angle=30))
print(figure.left_shoe(colour=Black, angle=10, part=FlipperThin))
print(figure.right_leg(colour=Yellow, angle=-10))
print(figure.right_shoe(colour=Black, angle=-10, part=FlipperThin))
print(figure.left_arm(colour=Yellow, angle=-45))
print(figure.left_hand(colour=Yellow, angle=10))
print(
    figure.left_hand_item(colour=Light_Grey, displacement=Vector(0, 0, -12), angle=-15, part=CameraMovie),
)  # Camera Movie
print(figure.right_arm(colour=Yellow, angle=60))
print(figure.right_hand(colour=Yellow, angle=0))
print()
print(Piece(colour=White, position=Vector(-50, -200, -50), rotation=Identity(), part="LIGHT"))
print(Piece(colour=White, position=Vector(50, -200, 0), rotation=Identity(), part="LIGHT"))
print(Piece(colour=White, position=Vector(0, -200, 50), rotation=Identity(), part="LIGHT"))

# Camera should be at 120.0,40.0,-200.0 in LDraw coordinates.
