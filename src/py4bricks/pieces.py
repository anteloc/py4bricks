"""pieces.py - Classes representing pieces and groups for LDraw.

- Piece: represents an LDraw part with a defined colour, position, and rotation.
- Group: represents a group of pieces, with a defined position and rotation that applies to all contained pieces.
"""
from __future__ import annotations

import re
from functools import reduce
from re import I
from typing import TYPE_CHECKING, Literal, Any

from collections.abc import Callable, Mapping

# pylint: disable=too-many-arguments, too-few-public-methods
from py4bricks.colour import Colour
from py4bricks.geometry import (
    LDU_PER_PLATE,
    LDU_PER_STUD_HEIGHT,
    LDU_PER_STUD,
    Identity,
    Matrix,
    Vector,
    ldu_to_studs, YAxis, orientation_to_rotation, studs_to_ldu, plates_to_ldu, ldu_to_plates
)
from py4bricks.library import get_dimensions
from py4bricks.library.colours import White
from py4bricks.library.parts.slopes import SlopeBrick451X1Double, SlopeBrick452X1, SlopeBrick452X1Double
from py4bricks.library.parts.tiles import Tile1X3

if TYPE_CHECKING:
    # The one and only Group lives in the llm layer. Imported for type hints
    # only — Piece duck-types group._adopt/.position/.rotation, so no runtime
    # import is needed (which also avoids a circular import: llm.group imports
    # this module).
    from py4bricks.llm.group import Group


# Defaults (see Piece.__init__):
#   x = ldu_x/2 - LDU_PER_STUD/2         # assumes LDraw origin at bbox centre in X
#   y = ldu_y - LDU_PER_STUD_HEIGHT      # assumes part has a 4-LDU stud on top
#   z = ldu_z/2 - LDU_PER_STUD/2         # assumes LDraw origin at bbox centre in Z
#
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
        
        dimensions = get_dimensions(part)
        self.ldu_x = dimensions.get("ldu_x", 0)
        self.ldu_y = dimensions.get("ldu_y", 0)
        self.ldu_z = dimensions.get("ldu_z", 0)
        self.studs_x = dimensions.get("studs_x", 0)
        self.studs_y = dimensions.get("studs_y", 0)
        self.plates_y = dimensions.get("plates_y", 0)
        self.studs_z = dimensions.get("studs_z", 0)

        # Offset from bottom-left-front origin to LDraw origin.
        # X/Z: leftmost-front footprint cell centroid → LDraw origin.
        #      Default assumes the LDraw origin is at the bbox centre
        # Y: bottom face → stud-base plane (LDraw origin sits at the top of the body,
        #    i.e. ldu_y minus the 4-LDU stud height).
        self.render_pos_offset = Vector(
            x=self.ldu_x / 2 - LDU_PER_STUD / 2,
            y=self.ldu_y - LDU_PER_STUD_HEIGHT,
            z=self.ldu_z / 2 - LDU_PER_STUD / 2,
        )

        # a placeholder to be set by subclasses to customize the visual final aspect of 
        # the piece by rotating it
        self.render_rot_offset = Identity()

        self.group = group
        if group:
            group._adopt(self)

    def render(self, position: Vector, rotation: Matrix) -> str:
        """Generate an LDraw type-1 line from pre-resolved world-space transforms.

        Called by Scene._resolve(), which composes the full transform chain before
        invoking this — keeping all matrix arithmetic out of LLM-generated scripts.
        """
        _rotation = rotation * self.render_rot_offset
        tup = tuple(reduce(lambda row1, row2: row1 + row2, _rotation.rows))
        origin = position + _rotation * self.render_pos_offset
        
        # print(f"Rendering piece {self.part} at {position} with rotation {rotation} and offset {self.offset}, resulting in origin {origin}")
        
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
            self.group._adopt(attached)
        return attached

    def displace_by(self, displacement: Vector) -> Piece:
        """Translate this piece by displacement in its local (group-relative) frame."""
        self.position = self.position + displacement
        return self

    def rotate_by(self, rotation: Matrix) -> Piece:
        """Post-multiply this piece's rotation matrix by the given rotation."""
        self.rotation = self.rotation * rotation
        return self

    def copy(self) -> Piece:
        """Create a copy of this piece with the same attributes but no group."""
        return Piece(
            colour=self.colour,
            position=self.position,
            rotation=self.rotation,
            part=self.part,
            group=None,
        )


class CustomPiece(Piece):
    """A Piece whose exposed position/rotation can be overridden and/or offset.
    """

    def __init__(self,
                 colour: Colour,
                 position: Vector = Vector(0, 0, 0),
                 rotation: Matrix = Identity(),
                 transform_by_rotating: Matrix = Identity(),
                 part: str = "",
                 group: Group | None = None,
                 override_render_pos_offset: dict[str, float] 
                    | Callable[[Piece], Mapping[str, float]] 
                    | None = None,
    ) -> None:
        self.transform_by_rotating = transform_by_rotating
        self.override_render_offset = override_render_pos_offset
        super().__init__(colour, position, rotation, part, group)
        
        # Apply rotation transform: dimensions change and the piece will also be rendered rotated
        self.render_rot_offset = transform_by_rotating
        self._transform_dimensions()

        if override_render_pos_offset is not None:
            _render_pos_offset = (override_render_pos_offset(self) # ty:ignore[call-top-callable]
                                if callable(override_render_pos_offset) 
                                else override_render_pos_offset)

            self.render_pos_offset = Vector(
                x=_render_pos_offset.get("x", self.render_pos_offset.x),
                y=_render_pos_offset.get("y", self.render_pos_offset.y),
                z=_render_pos_offset.get("z", self.render_pos_offset.z),
            )

    def _transform_dimensions(self) -> None:
        # treat dimensions as a vector for the vertex of the bounding box farthest from the origin, and rotate it by transform_by_rotating to get the new dimensions.
        original_dimensions = Vector(self.ldu_x, self.ldu_y, self.ldu_z)
        transformed_dimensions = self.transform_by_rotating * original_dimensions
        self.ldu_x = abs(transformed_dimensions.x)
        self.ldu_y = abs(transformed_dimensions.y)
        self.ldu_z = abs(transformed_dimensions.z)
        self.studs_x = ldu_to_studs(self.ldu_x)
        self.studs_y = ldu_to_studs(self.ldu_y)
        self.plates_y = ldu_to_plates(self.ldu_y)
        self.studs_z = ldu_to_studs(self.ldu_z)

    def copy(self) -> CustomPiece:
        return CustomPiece(
            colour=self.colour,
            position=self.position,
            rotation=self.rotation,
            transform_by_rotating=self.transform_by_rotating,
            part=self.part,
            group=None,
            override_render_pos_offset=self.override_render_offset,
        )
