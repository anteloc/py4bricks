"""pieces.py - Classes representing pieces and groups for LDraw.

- Piece: represents an LDraw part with a defined colour, position, and rotation.
- Group: represents a group of pieces, with a defined position and rotation that applies to all contained pieces.
"""
from __future__ import annotations

# pylint: disable=too-many-arguments, too-few-public-methods
from functools import reduce

from py4bricks.colour import Colour
from py4bricks.geometry import Identity, Matrix, Vector
from py4bricks.library import get_dimensions


class Piece:
    """A Piece is a Part with a defined colour, position, and rotation.
    
       Attributes:
            colour: the piece's colour representing an LDraw colour code
            position: the piece's position in its local (group-relative) frame
            rotation: the piece's orientation as a 3x3 rotation matrix
            part: the piece's LDraw part, with an associated variable defined under some e.g. library/parts/doors.py
            dimensions: the piece's dimensions, same as the part it represents, as a dict with keys "studs_x", "studs_y", "plates_y", "studs_z"
                studs_x: the piece's width in studs (x direction)
                studs_y: the piece's height in studs (y direction)
                plates_y: the piece's height in plates (y direction)
                studs_z: the piece's depth in studs (z direction)
            group: the Group this piece belongs to, or None if it is not in a group
    """

    def __init__(self, colour: Colour, position: Vector, rotation: Matrix, part: str, group: Group | None = None):
        self.position = position
        self.colour = colour
        self.rotation = rotation
        self.part = part.lower()
        self.dimensions = get_dimensions(self.part)
        self.studs_x = self.dimensions["studs_x"]
        self.studs_y = self.dimensions["studs_y"]
        self.plates_y = self.dimensions["plates_y"]
        self.studs_z = self.dimensions["studs_z"]
        self.group = group
        if group:
            group.add_piece(self)

    def __repr__(self) -> str:
        if self.group:
            position = self.group.position + self.group.rotation * self.position
            rotation = self.group.rotation * self.rotation
        else:
            position = self.position
            rotation = self.rotation
        tup = tuple(reduce(lambda row1, row2: row1 + row2, rotation.rows))
        return (
            ("1 %i " % self.colour.code)
            + ("%g " * 3) % (position.x, -position.y, position.z)
            + ("%g " * 9) % tup
            + ("%s.dat" % self.part)
        )

    def displace_by(self, displacement: Vector) -> None:
        """Translate this piece by displacement in its local (group-relative) frame."""
        self.position = self.position + displacement

    def rotate_by(self, rotation: Matrix) -> None:
        """Post-multiply this piece's rotation matrix by the given rotation."""
        self.rotation = self.rotation * rotation


class Group:
    """a Group of Pieces."""

    def __init__(
        self,
        position: Vector | None = None,
        rotation: Matrix | None = None,
    ) -> None:
        self.position = position if position is not None else Vector(0, 0, 0)
        self.rotation = rotation if rotation is not None else Identity()
        self.pieces: list[Piece] = []

    def __repr__(self) -> str:
        return "\n".join([repr(piece) for piece in self.pieces])

    def add_piece(self, piece: Piece) -> None:
        """Add a piece to the group."""
        self.pieces.append(piece)
        if piece.group and piece.group != self:
            piece.group.remove_piece(piece)
        piece.group = self

    def remove_piece(self, piece: Piece) -> None:
        """Remove a piece from the group."""
        self.pieces.remove(piece)
        piece.group = None

    def displace_by(self, displacement: Vector) -> None:
        """Translate this group in world space, moving all contained pieces with it."""
        self.position = self.position + displacement

    def rotate_by(self, rotation: Matrix) -> None:
        """Post-multiply this group's rotation matrix by the given rotation."""
        self.rotation = self.rotation * rotation
