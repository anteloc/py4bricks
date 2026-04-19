"""pieces.py - Classes representing pieces and groups for LDraw.

- Piece: represents an LDraw part with a defined colour, position, and rotation.
- Group: represents a group of pieces, with a defined position and rotation that applies to all contained pieces.
"""
from __future__ import annotations
from re import I

# pylint: disable=too-many-arguments, too-few-public-methods
from functools import reduce
from typing import Literal

from py4bricks.colour import Colour
from py4bricks.geometry import (
    LDU_PER_PLATE,
    LDU_PER_STUD_HEIGHT,
    LDU_PER_STUD,
    Identity,
    Matrix,
    Vector,
    ldu_to_studs, YAxis, orientation_to_rotation, studs_to_ldu, plates_to_ldu,
)
from py4bricks.library import get_dimensions


class Piece:
    """A Piece is a Part with a defined colour, position, and rotation."""

    @classmethod
    def attach_to(
        cls,
        piece: Piece,
        to: Piece,
        side: Literal["front", "back", "left", "right", "top", "bottom"],
        orientation: Literal["north", "south", "east", "west"] | None = None,
        right_studs: int = 0,
        back_studs: int = 0,
    ) -> Piece:
        """Attach piece to another piece by aligning it to the given side.

        Horizontal sides (position relative to to):
            - front:  negative Z direction
            - back:   positive Z direction
            - left:   negative X direction
            - right:  positive X direction

        Vertical sides (right_studs/back_studs shift within to's local frame):
            - top:    place piece flush on top of to
            - bottom: place piece flush under to

        orientation: final facing of the attached piece.
            None (default) inherits to's orientation — suitable for aligned
            structures like walls.  Specify explicitly when the piece must face
            a different direction (e.g. a corner column, an outward-facing window).
        """
        final_rot = orientation_to_rotation(orientation) if orientation else to.rotation

        match side:
            case "front":
                offset = Vector(0, 0, -piece.ldu_z)
            case "back":
                offset = Vector(0, 0, to.ldu_z)
            case "left":
                offset = Vector(-piece.ldu_x, 0, 0)
            case "right":
                offset = Vector(to.ldu_x, 0, 0)
            case "top":
                return Piece.place_on_top(
                    piece=piece, of=to,
                    right_studs=right_studs, back_studs=back_studs,
                    orientation=orientation,
                )
            case "bottom":
                of_body_half    = (to.ldu_y    - LDU_PER_STUD_HEIGHT) / 2
                piece_body_half = (piece.ldu_y - LDU_PER_STUD_HEIGHT) / 2
                piece.position  = to.position + to.rotation * Vector(
                    x=right_studs * LDU_PER_STUD,
                    y=-(of_body_half + piece_body_half),
                    z=back_studs  * LDU_PER_STUD,
                )
                piece.rotation = final_rot
                return piece
            case _:
                raise ValueError(f"Invalid side: {side}")

        piece.position = to.position + to.rotation * offset
        piece.rotation = final_rot
        return piece

    @classmethod
    def place_on_top(
        cls,
        piece: Piece,
        of: Piece,
        right_studs: int = 0,
        back_studs: int = 0,
        orientation: Literal["north", "south", "east", "west"] | None = None,
    ) -> Piece:
        """Place piece flush on top of another piece.

        right_studs / back_studs shift the new piece within of's local frame.
        orientation overrides the facing; None inherits of's orientation.
        """
        of_body_half    = (of.ldu_y    - LDU_PER_STUD_HEIGHT) / 2
        piece_body_half = (piece.ldu_y - LDU_PER_STUD_HEIGHT) / 2
        piece.position = of.position + of.rotation * Vector(
            x=right_studs * LDU_PER_STUD,
            y=of_body_half + piece_body_half,
            z=back_studs  * LDU_PER_STUD,
        )
        piece.rotation = orientation_to_rotation(orientation) if orientation else of.rotation
        return piece

    @classmethod
    def place_at(cls, 
                piece: Piece, 
                studs_x: int, 
                plates_y: int, 
                studs_z: int, 
                orientation: Literal["north", "south", "east", "west"] = "north"
    ) -> Piece:
        """Place piece at the given studs coordinates with the given rotation."""
        piece.rotation = orientation_to_rotation(orientation)
        x = studs_to_ldu(studs_x)
        y = plates_to_ldu(plates_y)
        z = studs_to_ldu(studs_z)
        piece.position = Vector(x, y, z)
        return piece

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

        # Offset from centroid-under-leftmost-stud origin to LDraw origin.
        # X/Z: leftmost-stud centroid → piece geometric center.
        # Y: body centroid → top face (includes stud protrusion).
        self.offset = Vector(
            x=self.ldu_x / 2 - LDU_PER_STUD / 2,
            y=self.ldu_y / 2 + LDU_PER_STUD_HEIGHT / 2,
            z=self.ldu_z / 2 - LDU_PER_STUD / 2,
        )

        self.group = group
        if group:
            group.add_piece(self)

    def render(self, position: Vector, rotation: Matrix) -> str:
        """Generate an LDraw type-1 line from pre-resolved world-space transforms.

        Called by Scene._resolve(), which composes the full transform chain before
        invoking this — keeping all matrix arithmetic out of LLM-generated scripts.
        """
        tup = tuple(reduce(lambda row1, row2: row1 + row2, rotation.rows))
        origin = position + rotation * self.offset
        return (
            ("1 %i " % self.colour.code)
            + ("%g " * 3) % (origin.x, -origin.y, origin.z)
            + ("%g " * 9) % tup
            + ("%s.dat" % self.part)
        )

    def __repr__(self) -> str:
        if self.group:
            position = self.group.position + self.group.rotation * self.position
            rotation = self.group.rotation * self.rotation
        else:
            position = self.position
            rotation = self.rotation
        return self.render(position, rotation)

    def attach(
        self,
        piece: Piece,
        side: Literal["front", "back", "left", "right", "top", "bottom"],
        orientation: Literal["north", "south", "east", "west"] | None = None,
        right_studs: int = 0,
        back_studs: int = 0,
    ) -> Piece:
        """Attach the given piece to this one on the given side.

        orientation overrides the attached piece's facing; None inherits this piece's.
        right_studs / back_studs are only meaningful for side="top" or "bottom".
        """
        attached = Piece.attach_to(
            piece=piece, to=self, side=side,
            orientation=orientation,
            right_studs=right_studs, back_studs=back_studs,
        )
        if self.group:
            self.group.add_piece(attached)
        return attached

    def displace_by(self, displacement: Vector) -> None:
        """Translate this piece by displacement in its local (group-relative) frame."""
        self.position = self.position + displacement

    def rotate_by(self, rotation: Matrix) -> None:
        """Post-multiply this piece's rotation matrix by the given rotation."""
        self.rotation = self.rotation * rotation

    def copy(self) -> Piece:
        """Create a copy of this piece with the same attributes but no group."""
        return Piece(
            colour=self.colour,
            position=self.position,
            rotation=self.rotation,
            part=self.part,
            group=None,
        )


class Group:
    """a Group of Pieces."""

    def __init__(
        self,
        position: Vector = Vector(0, 0, 0),
        rotation: Matrix = Identity(),
    ) -> None:
        self.position = position
        self.rotation = rotation
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
