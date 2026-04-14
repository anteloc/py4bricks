#!/usr/bin/env python

"""brothers.py - An example of figure construction.

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
from py4bricks.library.parts.minifig.accessories import CapWithLongFlatPeak
from py4bricks.library.parts.minifig.torsos import Torso
from py4bricks.pieces import Group

group = Group(position=Vector(0, 0, 0), rotation=Identity())

figure = Person(group=group)

print(figure.head(colour=Yellow))
print(figure.hat(colour=Green, part=CapWithLongFlatPeak))  # Cap
print(figure.torso(colour=Red, part=Torso))  # Torso
print(figure.left_arm(colour=Red))
print(figure.left_hand(colour=Yellow))
print(figure.right_arm(colour=Red, angle=-60))
print(figure.right_hand(colour=Yellow, angle=-10))
print(figure.hips(colour=Blue))
print(figure.left_leg(colour=Blue))
print(figure.right_leg(colour=Blue, angle=-30))

group.position = Vector(60, 0, 0)
group.rotation = Identity().rotate(-30, YAxis)
for piece in group.pieces:
    print(piece)

# print Piece(Grey, Vector(0, 72, 0), Identity(), "3867")

# Camera should be at 120.0,0.0,-200.0 in LDraw coordinates.
