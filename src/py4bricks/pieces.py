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

from py4bricks.geometry import (
    LDU_PER_BRICK_HEIGHT,
    LDU_PER_PLATE,
    LDU_PER_STUD,
    PLATES_PER_BRICK_HEIGHT,
    Identity,
    Vector,
    YAxis,
    brick_height_to_ldu,
    brick_height_to_plates,
    ldu_to_studs,
    plates_to_brick_height,
    plates_to_ldu,
    plates_to_studs,
    studs_to_ldu,
    studs_to_plates,
)


class Piece:
    """A Piece is a Part with a defined colour, position, and rotation."""

    def __init__(self, 
                 colour: Colour, 
                 position: Vector = Vector(0, 0, 0),
                 rotation: Matrix = Identity(),
                 part: str = "",
                 group: Group | None = None,
    ) -> None:
        self.position = position
        self.colour = colour
        self.rotation = rotation
        self.part = part.lower()
        self.dimensions = get_dimensions(part)
        self.ldu_x = self.dimensions.get("ldu_x", 0)
        self.ldu_y = self.dimensions.get("ldu_y", 0)
        self.ldu_z = self.dimensions.get("ldu_z", 0)
        self.studs_x = self.dimensions.get("studs_x", 0)
        self.studs_y = self.dimensions.get("studs_y", 0)
        self.plates_y = self.dimensions.get("plates_y", 0)
        self.studs_z = self.dimensions.get("studs_z", 0)

        self.offset = Vector(
            x=self.ldu_x / 2,
            y=self.ldu_y,
            z=self.ldu_z / 2,
        )

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

        # In LDraw, pieces have their origin at the center of the top face, 
        # but we are working with the piece's origin at the left-front-bottom-corner, 
        # so we need to apply an offset to get the correct position in LDraw coordinates.
        origin = position + self.offset

        return (
            ("1 %i " % self.colour.code)
            + ("%g " * 3) % (origin.x, -origin.y, origin.z)
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
        # Bounding box in group-local space, same attribute shape as Piece
        self.ldu_x: float = 0
        self.ldu_y: float = 0
        self.ldu_z: float = 0
        self.studs_x: int = 0
        self.plates_y: int = 0
        self.studs_z: int = 0

    def __repr__(self) -> str:
        return "\n".join([repr(piece) for piece in self.pieces])

    def _recalculate_dimensions(self) -> None:
        """Recompute the bounding box of all pieces in group-local space.

        Dimensions are expressed relative to the group origin, mirroring the
        attribute shape of Piece so callers can treat Group and Piece uniformly.
        """
        if not self.pieces:
            self.ldu_x = self.ldu_y = self.ldu_z = 0
            self.studs_x = self.plates_y = self.studs_z = 0
            return

        min_x = min(p.position.x for p in self.pieces)
        max_x = max(p.position.x + p.ldu_x for p in self.pieces)
        min_y = min(p.position.y for p in self.pieces)
        max_y = max(p.position.y + p.ldu_y for p in self.pieces)
        min_z = min(p.position.z for p in self.pieces)
        max_z = max(p.position.z + p.ldu_z for p in self.pieces)

        self.ldu_x = max_x - min_x
        self.ldu_y = max_y - min_y
        self.ldu_z = max_z - min_z
        self.studs_x = ldu_to_studs(self.ldu_x)
        # Floor division snaps to the plate grid, ignoring sub-plate stud protrusions
        # (e.g. Brick1X1 ldu_y=28 = 24 LDU body + 4 LDU stud; structural height is 24).
        self.plates_y = int(self.ldu_y // LDU_PER_PLATE)
        self.studs_z = ldu_to_studs(self.ldu_z)

    def add_piece(self, piece: Piece) -> None:
        """Add a piece to the group."""
        self.pieces.append(piece)
        if piece.group and piece.group != self:
            piece.group.remove_piece(piece)
        piece.group = self
        self._recalculate_dimensions()

    def remove_piece(self, piece: Piece) -> None:
        """Remove a piece from the group."""
        if piece is None:
            return
        self.pieces.remove(piece)
        piece.group = None
        self._recalculate_dimensions()

    def displace_by(self, displacement: Vector) -> None:
        """Translate this group in world space, moving all contained pieces with it."""
        self.position = self.position + displacement

    def rotate_by(self, rotation: Matrix) -> None:
        """Post-multiply this group's rotation matrix by the given rotation."""
        self.rotation = self.rotation * rotation
