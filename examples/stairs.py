#!/usr/bin/env python

"""stairs.py - An example using groups to duplicate parts of a scene.

Copyright (C) 2010 David Boddie <david@boddie.org.uk>

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
from py4bricks.geometry import Identity
from py4bricks.library.colours import *
from py4bricks.library.parts import Arch1X6, Brick1X1, Brick2X3, Plate6X6
from py4bricks.library.parts.minifig.accessories import ToolMagnifyingGlass
from py4bricks.library.parts.minifig.hats import TopHat
from py4bricks.library.parts.minifig.heads import HeadWithMonocle_Scar_AndMoustachePattern
from py4bricks.library.parts.minifig.torsos import (
    TorsoWithBlackSuit_RedShirt_GoldClaspsPattern,
)
from py4bricks.pieces import Group, Piece

group = Group(Vector(0, 0, -40), Identity())

figure = Person(group=group)
figure.head(colour=Yellow, part=HeadWithMonocle_Scar_AndMoustachePattern)
figure.hat(colour=Black, part=TopHat)
figure.torso(colour=Black, part=TorsoWithBlackSuit_RedShirt_GoldClaspsPattern)
figure.left_arm(colour=Black, angle=70)
figure.left_hand(colour=White, angle=0)
figure.right_arm(colour=Black, angle=-30)
figure.right_hand(colour=White, angle=0)

figure.right_hand_item(colour=Chrome_Silver, displacement=Vector(0, -58, -20), angle=0, part=ToolMagnifyingGlass)
figure.hips(colour=Black)
figure.left_leg(colour=Black, angle=50)
figure.right_leg(colour=Black, angle=-40)

group.position = Vector(-100, 40, -120)
group.rotation = Identity().rotate(-30, ZAxis).rotate(90, YAxis)
for piece in group.pieces:
    print(piece)

stairs = Group()

x = -120
y = 144
z = -160
steps = 5
Piece(colour=Dark_Blue, position=Vector(x, y, z + 40), rotation=Identity(), part=Plate6X6, group=stairs)
for i in range(steps):
    for pz in range(z, z + 120, 40):
        Piece(
            colour=Dark_Blue,
            position=Vector(x + 50 + (i * 40), y - 24 - (i * 24), pz),
            rotation=Identity(),
            part=Brick2X3,
            group=stairs,
        )

for piece in stairs.pieces:
    print(piece)

staircases = 7
for i in range(1, staircases + 1):
    stairs.position = Vector(0, i * (8 + steps * 24), 0)
    stairs.rotation = Identity().rotate(-90 * i, YAxis)
    for piece in stairs.pieces:
        print(piece)

top_y = y - (steps * 24) - 8
print(Piece(colour=Dark_Blue, position=Vector(120, top_y, -120), rotation=Identity(), part=Plate6X6))

for i in range(1, 5):
    print(Piece(colour=Dark_Red, position=Vector(170, top_y - (i * 24), -170), rotation=Identity(), part=Brick1X1))
    print(Piece(colour=Dark_Red, position=Vector(70, top_y - (i * 24), -170), rotation=Identity(), part=Brick1X1))

print(Piece(colour=Dark_Red, position=Vector(120, top_y - (5 * 24), -170), rotation=Identity(), part=Arch1X6))

print(Piece(colour=White, position=Vector(200, -200, 200), rotation=Identity(), part="LIGHT"))
print(Piece(colour=White, position=Vector(200, -200, -200), rotation=Identity(), part="LIGHT"))
print(Piece(colour=White, position=Vector(-200, -200, 200), rotation=Identity(), part="LIGHT"))
print(Piece(colour=White, position=Vector(-200, -200, -200), rotation=Identity(), part="LIGHT"))
