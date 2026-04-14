"""
Wall: rectangular brick wall
"""

from __future__ import annotations
from typing import Literal

from py4bricks.colour import Colour
from py4bricks.errors import BuilderError
from py4bricks.geometry import Identity, Vector, LDU_PER_STUD, LDU_PER_PLATE, YAxis
from py4bricks.library import get_dimensions
from py4bricks.pieces import Group, Piece

from py4bricks.library.parts.bricks import Brick1X1
from py4bricks.library.colours import White


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BRICK_HEIGHT_LDU    = 3 * LDU_PER_PLATE  # 1 brick row = 3 plates = 24 LDU
PLATES_PER_BRICK_ROW = 3                  # used to convert brick rows ↔ plates

# Rotation of the wall group for each cardinal facing direction (around Y axis).
# "north" is the default orientation: wall face looks toward -Z in LDraw space.
FACING_ROTATIONS = {
    "north": Identity(),
    "south": Identity().rotate(180, YAxis),
    "east":  Identity().rotate(90,  YAxis),
    "west":  Identity().rotate(-90, YAxis),
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

    The wall lives in its own local coordinate space:
      - X axis: along the wall face, 0 = left end, length = right end (studs)
      - Y axis: up from the wall base, 0 = bottom (plates)
      - Z axis: into the wall, 0 to depth_studs (derived from fill_part).

    Global positioning (where the wall sits in the scene) is handled by
    its parent Box or Group, not by the wall itself.

    """

    def __init__(
        self,
        length: int,
        height: int,
        facing: Literal["north", "south", "east", "west"],
        colour: Colour = White,
        name: str = "",
    ):
        """Create a wall.

        Args:
            length: Wall length in studs (along the face).
            height: Wall height in brick rows (1 row = 3 plates = 24 LDU).
            facing: "north", "south", "east", or "west".
            colour: LDraw colour code for the wall bricks.
            name: Unique identifier for this wall/Group.
        """
        super().__init__(rotation=FACING_ROTATIONS[facing])
        self.name   = name
        self.length = length
        self.height = height
        self.colour = colour

        # Fill the wall; track each fill brick by (col, row) for selective removal.
        self._fill: dict[tuple[int, int], Piece] = {}
        # Track inserted pieces as (x, y_brickrows, studs_x, plates_y) for overlap detection.
        self._insertions: list[tuple[int, int, int, int]] = []

        for row in range(height):
            for col in range(length):
                p = Piece(
                    colour=colour,
                    position=Vector(
                        x=col * LDU_PER_STUD,
                        y=-row * BRICK_HEIGHT_LDU,  # LDraw Y is negative-up
                        z=0,
                    ),
                    rotation=Identity(),
                    part=Brick1X1,
                    group=self,
                )
                self._fill[(col, row)] = p

    def insert(self, piece: Piece, x: int, y: int,
               colour: Colour | None = None) -> None:
        """Place a piece (e.g. window, door...) into an existing opening.

        Removes any fill bricks covered by the inserted piece's footprint, then
        places the piece at the given position.

        Args:
            piece: The Piece object to insert.
            x: Left edge in studs from the wall's left end.
            y: Bottom edge in brick rows from the wall base.
            colour: Brick colour. Defaults to the wall's own colour.

        Raises:
            BuilderError: If the piece overflows the wall bounds or overlaps
                          an already-inserted piece.
        """
        studs_x: int = piece.studs_x
        plates_y: int = piece.plates_y

        y_plates    = y * PLATES_PER_BRICK_ROW
        wall_plates = self.height * PLATES_PER_BRICK_ROW

        # --- bounds check ---
        if x < 0 or x + studs_x > self.length:
            msg = (
                f"{piece.part!r} overflows wall length "
                f"(x={x}, width={studs_x} studs, wall={self.length} studs)"
            )
            raise BuilderError(msg)
        if y < 0 or y_plates + plates_y > wall_plates:
            msg = (
                f"{piece.part!r} overflows wall height "
                f"(y={y}, height={plates_y} plates, wall={wall_plates} plates)"
            )
            raise BuilderError(msg)

        # --- overlap check against already-inserted pieces ---
        for (ix, iy, isx, ipy) in self._insertions:
            iy_plates = iy * PLATES_PER_BRICK_ROW
            x_overlap = x < ix + isx and x + studs_x > ix
            y_overlap = y_plates < iy_plates + ipy and y_plates + plates_y > iy_plates
            if x_overlap and y_overlap:
                msg = (
                    f"{piece.part!r} at (x={x}, y={y}) overlaps an existing insertion."
                )
                raise BuilderError(msg)

        # --- clear fill bricks covered by this piece ---
        # A fill brick at row r (3 plates tall) is covered if its range intersects
        # [y_plates, y_plates + plates_y).
        rows_covered = (plates_y + PLATES_PER_BRICK_ROW - 1) // PLATES_PER_BRICK_ROW
        for row in range(y, y + rows_covered):
            for col in range(x, x + studs_x):
                if fill_piece := self._fill.pop((col, row), None):
                    self.remove_piece(fill_piece)

        # --- place the piece in wall-local LDraw coordinates ---
        piece.position = Vector(
            x=x * LDU_PER_STUD,
            y=-y * BRICK_HEIGHT_LDU,  # LDraw Y is negative-up
            z=0,
        )
        if colour is not None:
            piece.colour = colour
        self.add_piece(piece)

        self._insertions.append((x, y, studs_x, plates_y))
