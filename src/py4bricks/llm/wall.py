"""
Wall: rectangular brick wall

A Wall is a rectangular surface of bricks, defined by:
  - length (studs along its face)
  - height (brick rows)
  - facing (north/south/east/west)
  - It lives in its own local coordinate space:
    - X axis: along the wall face, 0 = left end, length = right end (studs)
    - Y axis: up from the wall base, 0 = bottom (plates or bricks)
    - Z axis: wall thickness, depending on the bricks used (LDU)

Methods:
  - insert(piece, studs_x, plates_y/bricks_y) -> insert a piece (eg. window, door...) into the wall.
  - opening(studs_x, studs_width, plates_y/bricks_y, plates_height/bricks_height) -> create an opening in the wall.

"""

from __future__ import annotations

import sys
from typing import Literal

from py4bricks.colour import Colour
from py4bricks.errors import BuilderError
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
    ldu_to_plates,
    ldu_to_studs,
    plates_to_brick_height,
    plates_to_ldu,
    plates_to_studs,
    studs_to_ldu,
    studs_to_plates,
)
from py4bricks.library.colours import White
from py4bricks.library.parts.bricks import Brick1X1
from py4bricks.pieces import Group, Piece

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BRICK_HEIGHT_LDU    = 3 * LDU_PER_PLATE  # 1 brick row = 3 plates = 24 LDU
PLATE_HEIGHT_LDU    = LDU_PER_PLATE
PLATES_PER_BRICK_ROW = 3                  # used to convert brick rows ↔ plates

# Rotation of the wall group for each cardinal facing direction (around Y axis).
# "north" is the default orientation: wall face looks toward -Z in LDraw space.
FACING_ROTATIONS = {
    "north": Identity(),
    "south": Identity().rotate(-180, YAxis),
    "east":  Identity().rotate(-90,  YAxis),
    "west":  Identity().rotate(90, YAxis),
}


# ---------------------------------------------------------------------------
# Wall Class
# ---------------------------------------------------------------------------
# A Wall is a rectangular surface of bricks, defined by:
#   - length (studs along its face)
#   - height (brick rows)
#   - facing (north/south/east/west)

class Wall(Group):
    """A rectangular brick wall made of Brick1x1 pieces.

    A Wall is a Group, and as such can be conceived as:

        "A group of bricks and pieces that form a wall"

    The wall lives in its own local coordinate space:
      - X axis: along the wall face, 0 = left end, length = right end (studs)
      - Y axis: up from the wall base, 0 = bottom (plates or bricks)
      - Z axis: wall thickness, depending on the bricks used (LDU)

    Global positioning (where the wall sits in the scene) is handled by
    its Group superclass, while the Wall class focuses on managing the wall's 
    internal structure and the insertion of pieces (windows, doors...) into it.

    """

    def __init__(
        self,
        studs_width: int = 0,
        bricks_height: int = 0,
        plates_height: int = 0,
        same_width_as: Group | Piece | None = None,
        same_height_as: Group | Piece | None = None,
        name: str = "",
        colour: Colour = White,
        facing: Literal["north", "south", "east", "west"] = "north",
        position: Vector | None = None,
    ):
        """Create a wall.

        Args:
            studs_width: Wall width in studs (along the face). Mutually exclusive with same_width_as.
            bricks_height: Wall height in bricks (1 brick = 3 plates). Mutually exclusive with plates_height and same_height_as.
            plates_height: Wall height in plates. Mutually exclusive with bricks_height and same_height_as.
            same_width_as: Copy width (studs_x) from this Piece or Group. Mutually exclusive with studs_width.
            same_height_as: Copy height (plates_y) from this Piece or Group. Mutually exclusive with bricks_height and plates_height.
            facing: "north", "south", "east", or "west".
            colour: LDraw colour code for the wall bricks.
            name: Unique identifier for this wall/Group.
            position: World-space position of the wall's origin. Defaults to (0, 0, 0).
        """
        super().__init__(position=position, rotation=FACING_ROTATIONS[facing])
        self.name   = name
        self.colour = colour

        # --- resolve width ---
        width_sources = (studs_width > 0, same_width_as is not None)
        match width_sources:
            case (True, False):
                resolved_studs_width = studs_width
            case (False, True):
                resolved_studs_width = same_width_as.studs_x
            case (True, True):
                raise BuilderError("Specify studs_width or same_width_as, not both.")
            case _:
                raise BuilderError("Must specify either studs_width or same_width_as.")

        self.studs_length = resolved_studs_width

        # --- resolve height ---
        height_sources = (bricks_height > 0, plates_height > 0, same_height_as is not None)
        match height_sources:
            case (True, False, False):
                self.bricks_height = bricks_height
                self.plates_height = brick_height_to_plates(bricks_height)
            case (False, True, False):
                self.plates_height = plates_height
                self.bricks_height = plates_to_brick_height(plates_height)
            case (False, False, True):
                self.plates_height = same_height_as.plates_y
                self.bricks_height = plates_to_brick_height(self.plates_height)
            case (False, False, False):
                raise BuilderError("Must specify one of: bricks_height, plates_height, or same_height_as.")
            case _:
                raise BuilderError("Specify exactly one of: bricks_height, plates_height, or same_height_as.")


        # Fill the wall; track each fill brick by (col, row) for selective removal.
        self._fill: dict[tuple[int, int], Piece] = {}
        # Track inserted pieces as (x, y_brickrows, studs_x, plates_y) for overlap detection.
        self._insertions: list[tuple[int, int, int, int]] = []

        # Use bricks height for rows because a wall is made of bricks: 
        # there will be as much rows as height in bricks
        for row in range(self.bricks_height):
            for col in range(self.studs_length):
                p = Piece(
                    colour=colour,
                    position=Vector(
                        x=studs_to_ldu(col),
                        y=brick_height_to_ldu(row),
                        z=0,
                    ),
                    rotation=Identity(),
                    part=Brick1X1,
                    group=self,
                )
                self._fill[(col, row)] = p

    def insert(self, piece: Piece, studs_x: int, plates_y: int = -1, bricks_y: int = -1,
               colour: Colour | None = None) -> None:
        """Place a piece (e.g. window, door...) and remove bricks to make room for it.

        Removes any fill bricks covered by the inserted piece's footprint, then
        places the piece at the given position.

        Args:
            piece: The Piece object to insert.
            studs_x: Insert position x in studs from the wall's left end.
            plates_y: Insert position y in plates from the wall base.
            bricks_y: Insert position y in brick rows from the wall base (alternative to plates_y).
            colour: Brick colour. Defaults to the wall's own colour.

        Raises:
            BuilderError: If the piece overflows the wall bounds or overlaps
                          an already-inserted piece.
        """
        if plates_y >= 0 and bricks_y >= 0:
            raise BuilderError("Cannot specify both plates_y and bricks_y.")

        if bricks_y >= 0:
            plates_y = brick_height_to_plates(bricks_y)
        elif plates_y >= 0:
            bricks_y = plates_to_brick_height(plates_y)
        else:
            raise BuilderError("Must specify either plates_y or bricks_y.")

        p_bricks_y: int = plates_to_brick_height(piece.plates_y)
        # avoid removing the upper row due to studs from the piece taking space upwards
        opening_bricks_height = p_bricks_y - 1

        self.opening(studs_x=studs_x, studs_width=piece.studs_x, 
                     bricks_y=bricks_y, bricks_height=opening_bricks_height)

        p_x = studs_to_ldu(studs_x)
        p_y = plates_to_ldu(plates_y)

        # --- place the piece in wall-local coordinates ---
        piece.position = Vector(
            x=p_x,  # center the piece on the studs_x position
            y=p_y,  # center the piece on the plates_y position
            z=0,
        )

        if colour is not None:
            piece.colour = colour
        self.add_piece(piece)

        self._insertions.append((studs_x, plates_y, piece.studs_x, piece.plates_y))

    def opening(self, studs_x: int, studs_width: int, 
                plates_y: int = -1, plates_height: int = 0, 
                bricks_y: int = -1, bricks_height: int = 0) -> None:
        """Create an opening with the given width and height by removing bricks starting at (studs_x, plates_y/bricks_y).

        Args:
            studs_x: Opening start position x in studs from the wall's left end.
            studs_width: Opening width in studs.
            plates_y: Opening start position y in plates from the wall base.
            plates_height: Opening height in plates from the wall base.
            bricks_y: Opening start position y in brick rows from the wall base (alternative to plates_y).
            bricks_height: Opening height in brick rows from the wall base (alternative to plates_height).

        Raises:
            BuilderError: If the piece overflows the wall bounds or overlaps
                          an already-inserted piece.
        """
        if plates_y >= 0 and bricks_y >= 0:
            raise BuilderError("Cannot specify both plates_y and bricks_y.")

        if plates_height > 0 and bricks_height > 0:
            raise BuilderError("Cannot specify both plates_height and bricks_height.")

        if bricks_y >= 0:
            plates_y = brick_height_to_plates(bricks_y)
        elif plates_y >= 0:
            bricks_y = plates_to_brick_height(plates_y)
        else:
            raise BuilderError("Must specify either plates_y or bricks_y.")

        if bricks_height > 0:
            plates_height = brick_height_to_plates(bricks_height)
        elif plates_height > 0:
            bricks_height = plates_to_brick_height(plates_height)
        else:
            raise BuilderError("Must specify either plates_height or bricks_height.")
        
        # Use bricks height for rows because a wall is made of bricks: 
        # there will be as much rows as height in bricks
        for row in range(bricks_y, bricks_y + bricks_height):
            for col in range(studs_x, studs_x + studs_width):
                p = self._fill.pop((col, row), None)
                if p is not None:
                    self.remove_piece(p)

