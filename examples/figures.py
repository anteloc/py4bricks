#!/usr/bin/env python

"""figures.py - An example of figure construction.

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
from py4bricks.library.parts import Baseplate16X16, Rock1X1Crystal5Point
from py4bricks.library.parts.minifig.accessories import (
    HelmetClassicWithThickChinGuardAndVisorDimples as HelmetClassic,
)
from py4bricks.library.parts.minifig.accessories import (
    MetalDetector,
    Torch,
)
from py4bricks.library.parts.minifig.torsos import TorsoWithClassicSpacePattern
from py4bricks.pieces import Piece

figure = Person(Vector(0, 0, -10))
print(figure.head(colour=Yellow, angle=30))
print(figure.hat(colour=White, part=HelmetClassic))
print(figure.torso(colour=White, part=TorsoWithClassicSpacePattern))
print(figure.backpack(colour=White, displacement=Vector(0, -2, 0)))
print(figure.hips_and_legs(colour=White))
print(figure.left_arm(colour=White, angle=-45))
print(figure.left_hand(colour=White, angle=0))
print(figure.left_hand_item(colour=Light_Grey, displacement=Vector(0, -11, -12), angle=0, part=Torch))  # Torch
print(figure.right_arm(colour=White, angle=0))
print(figure.right_hand(colour=White, angle=0))
print(
    figure.right_hand_item(colour=Light_Grey, displacement=Vector(0, -23, -12), angle=90, part=MetalDetector),
)  # Metal detector

figure = Person(Vector(97.5, 0, 57.5), Identity().rotate(45, YAxis))
print(figure.head(colour=Yellow, angle=-15))
print(figure.hat(colour=Red, part=HelmetClassic))
print(figure.torso(colour=Red, part=TorsoWithClassicSpacePattern))
print(figure.backpack(colour=Red, displacement=Vector(0, -2, 0)))
print(figure.hips(colour=Red))
print(figure.left_leg(colour=Red, angle=-55))
print(figure.right_leg(colour=Red, angle=0))
print(figure.left_arm(colour=Red, angle=-45))
print(figure.left_hand(colour=Red, angle=0))
print(figure.right_arm(colour=Red, angle=-30))
print(figure.right_hand(colour=Red, angle=0))
print(figure.right_hand_item(colour=Light_Grey, displacement=Vector(0, -11, -12), angle=0, part=Torch))  # Torch
print()
print(Piece(colour=Light_Grey, position=Vector(0, 72, 0), rotation=Identity(), part=Baseplate16X16))
print(Piece(colour=Light_Grey, position=Vector(60, 72, -60), rotation=Identity(), part=Rock1X1Crystal5Point))

# Camera should be at 160.0,-80.0,-240.0 in LDraw coordinates.
