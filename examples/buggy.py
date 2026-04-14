#!/usr/bin/env python

"""buggy.py - An example of materials.

Copyright (C) 2009 David Boddie <david@boddie.org.uk>

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
from py4bricks.geometry import YAxis
from py4bricks.library.colours import *
from py4bricks.library.parts import (
    Antenna4HWithRoundedTop,
    Baseplate16X16,
    Brick1X2WithClassicSpaceLogoPattern,
    CarSteeringStandAndWheel_Complete_,
    Plate2X2,
    Plate2X2WithRedWheels_Complete_,
    SlopeBrick452X2,
    Tyre6_50X8OffsetTread,
)
from py4bricks.library.parts.minifig.accessories import Seat2X2
from py4bricks.pieces import Group, Piece

figure = Person(position=Vector(0, 0, -10))
print(figure.head(colour=Yellow, angle=30))
print(figure.hat(colour=White, part="193B"))
print(figure.torso(colour=White, part="973P90"))
print(figure.backpack(colour=White, displacement=Vector(0, 2, 0)))
print(figure.hips(colour=White))
print(figure.left_leg(colour=White, angle=0))
print(figure.right_leg(colour=White, angle=0))
print(figure.left_arm(colour=White, angle=-45))
print(figure.left_hand(colour=White, angle=0))
print(figure.left_hand_item(colour=Light_Grey, displacement=Vector(0, 11, -12), angle=0, part="3959"))
print(figure.right_arm(colour=White, angle=0))
print(figure.right_hand(colour=White, angle=0))

rover = Group(position=Vector(0, -48, 60), rotation=Identity().rotate(-15, YAxis))
print(
    Piece(
        colour=Light_Grey,
        position=Vector(0, 0, 0),
        rotation=Identity(),
        part=Plate2X2WithRedWheels_Complete_,
        group=rover,
    ),
)
print(
    Piece(
        colour=Rubber_Black,
        position=Vector(30, -6, 0),
        rotation=Identity().rotate(90, YAxis),
        part=Tyre6_50X8OffsetTread,
        group=rover,
    ),
)
print(
    Piece(
        colour=Rubber_Black,
        position=Vector(-30, -6, 0),
        rotation=Identity().rotate(90, YAxis),
        part=Tyre6_50X8OffsetTread,
        group=rover,
    ),
)
print(
    Piece(
        colour=Light_Grey,
        position=Vector(0, 0, -80),
        rotation=Identity(),
        part=Plate2X2WithRedWheels_Complete_,
        group=rover,
    ),
)
print(
    Piece(
        colour=Rubber_Black,
        position=Vector(30, -6, -80),
        rotation=Identity().rotate(90, YAxis),
        part=Tyre6_50X8OffsetTread,
        group=rover,
    ),
)
print(
    Piece(
        colour=Rubber_Black,
        position=Vector(-30, -6, -80),
        rotation=Identity().rotate(90, YAxis),
        part=Tyre6_50X8OffsetTread,
        group=rover,
    ),
)

print(Piece(colour=Light_Grey, position=Vector(0, 0, -40), rotation=Identity(), part=Plate2X2, group=rover))

print(
    Piece(
        colour=Chrome_Silver,
        position=Vector(0, 24, -10),
        rotation=Identity().rotate(180, YAxis),
        part=SlopeBrick452X2,
        group=rover,
    ),
)
print(
    Piece(
        colour=Chrome_Silver,
        position=Vector(0, 32, -10),
        rotation=Identity().rotate(180, YAxis),
        part=CarSteeringStandAndWheel_Complete_,
        group=rover,
    ),
)
print(
    Piece(
        colour=Chrome_Gold,
        position=Vector(0, 24, -60),
        rotation=Identity().rotate(180, YAxis),
        part=Seat2X2,
        group=rover,
    ),
)
print(Piece(colour=Chrome_Gold, position=Vector(0, 8, -60), rotation=Identity(), part=Plate2X2, group=rover))
print(Piece(colour=Chrome_Gold, position=Vector(0, 16, -60), rotation=Identity(), part=Plate2X2, group=rover))
print(
    Piece(
        colour=Chrome_Gold,
        position=Vector(0, 24, -90),
        rotation=Identity(),
        part=Brick1X2WithClassicSpaceLogoPattern,
        group=rover,
    ),
)
print(
    Piece(
        colour=Chrome_Silver,
        position=Vector(-10, 32, -90),
        rotation=Identity(),
        part=Antenna4HWithRoundedTop,
        group=rover,
    ),
)

print(Piece(colour=Yellow, position=Vector(0, -72, 0), rotation=Identity(), part=Baseplate16X16))
print(Piece(colour=Yellow, position=Vector(0, -72, -320), rotation=Identity(), part=Baseplate16X16))
print(Piece(colour=Blue, position=Vector(320, -72, 0), rotation=Identity(), part=Baseplate16X16))
print(Piece(colour=Blue, position=Vector(320, -72, -320), rotation=Identity(), part=Baseplate16X16))
print(Piece(colour=White, position=Vector(-90, 150, 90), rotation=Identity(), part="LIGHT"))
print(Piece(colour=White, position=Vector(90, 150, 90), rotation=Identity(), part="LIGHT"))
