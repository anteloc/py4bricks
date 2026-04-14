"""figure.py - Mini-figure construction classes for the ldraw Python package.

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

# pylint: disable=missing-docstring
from py4bricks.colour import Colour
from py4bricks.geometry import Identity, Matrix, Vector, XAxis, YAxis, ZAxis
from py4bricks.pieces import Group, Piece


def dependent_piece(dep):
    """Mark a piece method as dependent on another piece existing."""

    def decorator(fn):
        def wrapped(self, *args, **kwargs):
            try:
                dependent_object = self.pieces_info[dep]
                return fn(self, *args, **{dep: dependent_object, **kwargs})
            except KeyError:
                return None

        return wrapped

    return decorator


# hardcoded
Airtanks = "3838"
HipsAndLegs = "3815c01"
Hips = "3815b"
ArmLeft = "3819"
ArmRight = "3818"
Hand = "3820"
LegLeft = "3817b"
LegRight = "3816b"
Torso = "973"
Head = HeadWithSwSmirkAndBrownEyebrowsPattern = "3626bps5"


class Person:
    """Representation of a LEGO minifigure."""

    def __init__(
        self,
        position: Vector | None = None,
        rotation: Matrix | None = None,
        group: Group | None = None,
    ):
        self.position: Vector = position if position is not None else Vector(0, 0, 0)
        self.rotation: Matrix = rotation if rotation is not None else Identity()
        self.pieces_info = {}
        self.group = group

    def head(self, colour: Colour, angle: int=0, part: str=Head):
        """Displacement from torso."""
        displacement: Vector = self.rotation * Vector(0, 24, 0)
        piece = Piece(
            colour=colour,
            position=self.position + displacement,
            rotation=self.rotation * Identity().rotate(-angle, YAxis), # type: ignore
            part=part,
            group=self.group,
        )
        self.pieces_info["head"] = piece
        return piece

    @dependent_piece("head")
    def hat(self, colour: Colour, head: Piece = None,  # type: ignore[assignment]
            part: str="3901"):
        """Add a hat piece to the figure's head."""
        # Displacement from head
        displacement: Vector = head.position + head.rotation * Vector(0, 0, 0) # type: ignore
        return Piece(colour=colour, position=displacement, rotation=head.rotation, part=part, group=self.group) # type: ignore

    def torso(self, colour: Colour, part: str=Torso):
        """Torso piece."""
        return Piece(colour=colour, position=self.position, rotation=self.rotation, part=part, group=self.group)

    def backpack(self, colour: Colour, displacement: Vector | None = None, part: str=Airtanks):
        """Displacement from torso."""
        _displacement: Vector = self.rotation * (
            displacement if displacement is not None else Vector(0, 0, 0)
        )
        return Piece(
            colour=colour,
            position=self.position + _displacement,
            rotation=self.rotation,
            part=part,
            group=self.group,
        )

    def hips_and_legs(self, colour: Colour, part: str=HipsAndLegs):
        """Displacement from torso."""
        displacement: Vector = self.rotation * Vector(0, -32, 0)
        return Piece(
            colour=colour,
            position=self.position + displacement,
            rotation=self.rotation,
            part=part,
            group=self.group,
        )

    def hips(self, colour: Colour, part: str=Hips):
        """Displacement from torso."""
        displacement: Vector = self.rotation * Vector(0, -32, 0)
        return Piece(
            colour=colour,
            position=self.position + displacement,
            rotation=self.rotation,
            part=part,
            group=self.group,
        )

    def left_arm(self, colour: Colour, angle: int=0, part: str=ArmLeft):
        """Displacement from torso."""
        displacement: Vector = self.rotation * Vector(15, -8, 0)
        piece = Piece(
            colour=colour,
            position=self.position + displacement,
            rotation=self.rotation
                        * Identity().rotate(-10, ZAxis)
                        * Identity().rotate(angle, XAxis),
            part=part,
            group=self.group,
        )
        self.pieces_info["left_arm"] = piece
        return piece

    @dependent_piece("left_arm")
    def left_hand(self, colour: Colour, left_arm: Piece = None,  # type: ignore[assignment]
                  angle: int=0, part: str=Hand):
        """Add a left hand piece to the figure's left arm."""
        # Displacement from left hand
        displacement: Vector = left_arm.position + left_arm.rotation * Vector(4, -17, -9)
        rotation: Matrix = (
            left_arm.rotation
            * Identity().rotate(40, XAxis)
            * Identity().rotate(angle, ZAxis)
        )
        piece = Piece(colour=colour, position=displacement, rotation=rotation, part=part, group=self.group)
        self.pieces_info["left_hand"] = piece
        return piece

    @dependent_piece("left_hand")
    def left_hand_item(
        self, colour: Colour, left_hand: Piece = None,  # type: ignore[assignment]
        displacement: Vector | None=None, angle: int=0, part: str | None=None,
    ):
        """Displacement from left hand."""
        if not part:
            return None
        _offset: Vector = displacement if displacement is not None else Vector(0, 0, 0)
        _displacement: Vector = left_hand.position + left_hand.rotation * _offset
        rotation: Matrix = (
            left_hand.rotation
            * Identity().rotate(10, XAxis)
            * Identity().rotate(-angle, YAxis)
        )
        return Piece(
            colour=colour, position=_displacement, rotation=rotation,
            part=part, group=self.group,
        )

    def right_arm(self, colour: Colour, angle: int=0, part: str=ArmRight):
        """Displacement from torso."""
        displacement: Vector = self.rotation * Vector(-15, -8, 0)
        piece = Piece(
            colour=colour,
            position=self.position + displacement,
            rotation=self.rotation
                        * Identity().rotate(10, ZAxis)
                        * Identity().rotate(angle, XAxis),
            part=part,
            group=self.group,
        )
        self.pieces_info["right_arm"] = piece
        return piece

    @dependent_piece("right_arm")
    def right_hand(self, colour: Colour, right_arm: Piece = None,  # type: ignore[assignment]
                   angle: int=0, part: str=Hand):
        """Add a right hand piece to the figure's right arm."""
        displacement: Vector = right_arm.position + right_arm.rotation * Vector(-4, -17, -9)
        rotation: Matrix = (
            right_arm.rotation
            * Identity().rotate(40, XAxis)
            * Identity().rotate(angle, ZAxis)
        )
        piece = Piece(colour=colour, position=displacement, rotation=rotation, part=part, group=self.group)
        self.pieces_info["right_hand"] = piece
        return piece

    @dependent_piece("right_hand")
    def right_hand_item(
        self, colour: Colour, right_hand: Piece = None,  # type: ignore[assignment]
        displacement: Vector | None=None, angle: int=0, part: str | None=None,
    ):
        """Add a right hand item."""
        if not part:
            return None
        _offset: Vector = displacement if displacement is not None else Vector(0, 0, 0)
        _displacement: Vector = right_hand.position + right_hand.rotation * _offset
        rotation: Matrix = (
            right_hand.rotation
            * Identity().rotate(10, XAxis)
            * Identity().rotate(-angle, YAxis)
        )
        return Piece(
            colour=colour, position=_displacement, rotation=rotation,
            part=part, group=self.group,
        )

    def left_leg(self, colour: Colour, angle: int=0, part: str=LegLeft):
        """Add a left leg."""
        displacement: Vector = self.rotation * Vector(0, -44, 0)
        piece = Piece(
            colour=colour,
            position=self.position + displacement,
            rotation=self.rotation * Identity().rotate(angle, XAxis),
            part=part,
            group=self.group,
        )
        self.pieces_info["left_leg"] = piece
        return piece

    @dependent_piece("left_leg")
    def left_shoe(self, colour: Colour, left_leg: Piece = None,  # type: ignore[assignment]
                  angle: int=0, part: str | None=None):
        """Add a shoe on the left."""
        if not part:
            return None
        # Displacement from left leg
        displacement: Vector = left_leg.position + left_leg.rotation * Vector(10, -28, 0)
        rotation: Matrix = left_leg.rotation * Identity().rotate(-angle, YAxis)
        return Piece(colour=colour, position=displacement, rotation=rotation, part=part, group=self.group)

    def right_leg(self, colour: Colour, angle: int=0, part: str=LegRight):
        """Add a right leg."""
        displacement: Vector = self.rotation * Vector(0, -44, 0)
        piece = Piece(
            colour=colour,
            position=self.position + displacement,
            rotation=self.rotation * Identity().rotate(angle, XAxis),
            part=part,
            group=self.group,
        )
        self.pieces_info["right_leg"] = piece
        return piece

    @dependent_piece("right_leg")
    def right_shoe(self, colour: Colour, right_leg: Piece = None,  # type: ignore[assignment]
                   angle: int=0, part: str | None=None):
        """Add a shoe on the right."""
        if not part:
            return None
        # Displacement from right leg
        displacement: Vector = right_leg.position + right_leg.rotation * Vector(-10, -28, 0)
        rotation: Matrix = right_leg.rotation * Identity().rotate(-angle, YAxis)
        return Piece(colour=colour, position=displacement, rotation=rotation, part=part, group=self.group)