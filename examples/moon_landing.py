#!/usr/bin/env python

"""moon_landing.py - An example of figure construction.

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
from py4bricks.library.colours import (
    Black,
    Green,
    Light_Grey,
    Red,
    Trans_Green,
    White,
    Yellow,
)
from py4bricks.library.parts import (
    Antenna4HWithRoundedTop,
    Baseplate32X32WithCraters,
    Brick1X1RoundWithSolidStud,
    Brick1X2WithClassicSpaceLogoPattern,
    CarSteeringStandAndWheel_Complete_,
    Plate2X2,
    Plate2X2WithRedWheels_Complete_,
    SlopeBrick452X2,
    Tyre6_50X8OffsetTread,
)
from py4bricks.library.parts.minifig.accessories import (
    HelmetClassicWithThickChinGuardAndVisorDimples as HelmetClassic,
)
from py4bricks.library.parts.minifig.accessories import (
    Seat2X2,
    Torch,
)
from py4bricks.library.parts.minifig.torsos import TorsoWithClassicSpacePattern
from py4bricks.pieces import Group, Piece

figure = Person(position=Vector(0, 0, -10))
print(figure.head(colour=Yellow, angle=30))
print(figure.hat(colour=White, part=HelmetClassic))
print(figure.torso(colour=White, part=TorsoWithClassicSpacePattern))
print(figure.backpack(colour=White, displacement=Vector(0, -2, 0)))
print(figure.hips(colour=White))
print(figure.left_leg(colour=White, angle=0))
print(figure.right_leg(colour=White, angle=0))
print(figure.left_arm(colour=White, angle=-45))
print(figure.left_hand(colour=White, angle=0))
print(figure.left_hand_item(colour=Light_Grey, displacement=Vector(0, -11, -12), angle=0, part=Torch))  # Torch
print(figure.right_arm(colour=White, angle=0))
print(figure.right_hand(colour=White, angle=0))
print()
rover = Group(position=Vector(80, -48, 20), rotation=Identity())

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
        colour=Black,
        position=Vector(30, -6, 0),
        rotation=Identity().rotate(-90, YAxis),
        part=Tyre6_50X8OffsetTread,
        group=rover,
    ),
)
print(
    Piece(
        colour=Black,
        position=Vector(-30, -6, 0),
        rotation=Identity().rotate(-90, YAxis),
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
        colour=Black,
        position=Vector(30, -6, -80),
        rotation=Identity().rotate(-90, YAxis),
        part=Tyre6_50X8OffsetTread,
        group=rover,
    ),
)
print(
    Piece(
        colour=Black,
        position=Vector(-30, -6, -80),
        rotation=Identity().rotate(-90, YAxis),
        part=Tyre6_50X8OffsetTread,
        group=rover,
    ),
)

print(Piece(colour=Light_Grey, position=Vector(0, 0, -40), rotation=Identity(), part=Plate2X2, group=rover))

print(
    Piece(
        colour=Light_Grey,
        position=Vector(0, 24, -10),
        rotation=Identity().rotate(-180, YAxis),
        part=SlopeBrick452X2,
        group=rover,
    ),
)
print(
    Piece(
        colour=Light_Grey,
        position=Vector(0, 32, -10),
        rotation=Identity().rotate(-180, YAxis),
        part=CarSteeringStandAndWheel_Complete_,
        group=rover,
    ),
)
print(
    Piece(
        colour=Light_Grey,
        position=Vector(0, 24, -60),
        rotation=Identity().rotate(-180, YAxis),
        part=Seat2X2,
        group=rover,
    ),
)
print(Piece(colour=Light_Grey, position=Vector(0, 8, -60), rotation=Identity(), part=Plate2X2, group=rover))
print(Piece(colour=Light_Grey, position=Vector(0, 16, -60), rotation=Identity(), part=Plate2X2, group=rover))
print(
    Piece(
        colour=Light_Grey,
        position=Vector(0, 24, -90),
        rotation=Identity(),
        part=Brick1X2WithClassicSpaceLogoPattern,
        group=rover,
    ),
)
print(
    Piece(
        colour=Light_Grey,
        position=Vector(-10, 32, -90),
        rotation=Identity(),
        part=Antenna4HWithRoundedTop,
        group=rover,
    ),
)
print(
    Piece(
        colour=Trans_Green,
        position=Vector(10, 48, -90),
        rotation=Identity(),
        part=Brick1X1RoundWithSolidStud,
        group=rover,
    ),
)
print(Piece(colour=Green, position=Vector(10, 52, -90), rotation=Identity(), part="LIGHT", group=rover))

# Duplicate the rover with a different position and orientation.

rover.position = Vector(-85, -45, 115)
rover.rotation = Identity().rotate(190, YAxis).rotate(-20, XAxis).rotate(-6, ZAxis)
print(rover)

# Add a seated figure to the rover.

figure = Person(position=Vector(0, 76, -50), rotation=Identity().rotate(-180, YAxis), group=rover)
print(figure.head(colour=Yellow, angle=0))
print(figure.hat(colour=Red, part=HelmetClassic))
print(figure.torso(colour=Red, part=TorsoWithClassicSpacePattern))
print(figure.backpack(colour=Red, displacement=Vector(0, -2, 0)))
print(figure.hips(colour=Red))
print(figure.left_leg(colour=Red, angle=-90))
print(figure.right_leg(colour=Red, angle=-90))
print(figure.left_arm(colour=Red, angle=-35))
print(figure.left_hand(colour=Red, angle=0))
print(figure.right_arm(colour=Red, angle=-35))
print(figure.right_hand(colour=Red, angle=0))
print()
print(Piece(colour=White, position=Vector(200, 300, -400), rotation=Identity(), part="LIGHT"))
print(Piece(colour=Light_Grey, position=Vector(0, -72, 0), rotation=Identity(), part=Baseplate32X32WithCraters))
