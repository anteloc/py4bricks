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
    Origin,
    Plane3D,
    Vector,
    XAxis,
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
from py4bricks.library.colours import White, Medium_Azure
from py4bricks.library.parts.bricks import Brick1X1
from py4bricks.library.parts.cones import Cone1X1
from py4bricks.library.parts.bars import Spike2_4LWith4FinsWithBar0_4L
from py4bricks.pieces import Group, Piece

from py4bricks.utils import single_value_or_error

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
    @classmethod
    def from_dimensions(cls, 
                        name: str, 
                        studs_width: int, 
                        bricks_height: int = 0, 
                        plates_height: int = 0, 
                        colour: Colour = White,
    ) -> Wall:
        """Create a wall from explicit dimensions."""
        return cls(name=name, 
                   studs_width=studs_width, 
                   bricks_height=bricks_height, 
                   plates_height=plates_height, 
                   colour=colour, 
                )
    
    @classmethod
    def from_references(cls, 
                       name: str, 
                       same_width_as: Group | Piece, 
                       same_height_as: Group | Piece, 
                       colour: Colour = White, 
    ) -> Wall:
        """Create a wall by copying dimensions from reference objects."""
        return cls(name=name, 
                   studs_width=same_width_as.studs_x, 
                   plates_height=same_height_as.plates_y, 
                   colour=colour, 
                )

    def __init__(
        self,
        name: str,
        studs_width: int = 0,
        bricks_height: int = 0,
        plates_height: int = 0,
        position: Vector = Origin(),
        facing: Literal["north", "south", "east", "west"] = "north",
        colour: Colour = White,
    ):
        """Create a wall.

        Args:
            name: Unique identifier for this wall/Group.
            studs_width: Wall width in studs (along the face). Mutually exclusive with same_width_as.
            bricks_height: Wall height in bricks (1 brick = 3 plates). Mutually exclusive with plates_height and same_height_as.
            plates_height: Wall height in plates. Mutually exclusive with bricks_height and same_height_as.
            position: World-space position of the wall's origin. Mutually exclusive with parallel_to.
            facing: "north", "south", "east", or "west". Ignored when parallel_to is given (facing is inherited).
            colour: LDraw colour code for the wall bricks.
        """

        # Enable for debugging: visual cues, etc.
        self.debug = True

        self.facing = facing
        super().__init__(position=position, rotation=FACING_ROTATIONS[facing])
        self.name   = name
        self.colour = colour

        self.studs_width = studs_width

        height_values = (
            plates_height,
            brick_height_to_plates(bricks_height),
        )

        self.plates_height = single_value_or_error(
            height_values,
            non_value=0,
            param_name="height (plates)",
        )

        self.bricks_height = plates_to_brick_height(self.plates_height)

        # Fill the wall; track each fill brick by (col, row) for selective removal.
        self._fill: dict[tuple[int, int], Piece] = {}
        # TODO Track inserted pieces as (x, y_brickrows, studs_x, plates_y) for overlap detection.
        self._insertions: list[tuple[int, int, int, int]] = []

        # Use bricks height for rows because a wall is made of bricks: 
        # there will be as much rows as height in bricks
        self._fill_region(
            studs_x_start=0,
            studs_x_end=studs_width,
            bricks_y_start=0,
            bricks_y_end=self.bricks_height,
        )

        if self.debug:
            self._debug_hints()
            
    def _debug_hints(self):
        """Enable debug visual cues to understand wall positioning and orientation."""
        # first brick color tells us where the wall starts to be built (studs_x=0, bricks_y=0)
        self._fill[(0, 0)].colour = Medium_Azure
        plane_normal = self._wall_plane().normal
        wall_normal = plane_normal / plane_normal.magn()
        facing_arrow = Piece(
            colour=Medium_Azure,
            position=wall_normal + Vector(0, 0, studs_to_ldu(4)),
            rotation=Identity().rotate(-90, XAxis),  # rotate to point along the wall plane instead of upwards
            part=Spike2_4LWith4FinsWithBar0_4L,
            group=self)
        return [facing_arrow]

    def _fill_region(self, 
                     studs_x_start: int, 
                     studs_x_end: int, 
                     bricks_y_start: int, 
                     bricks_y_end: int
    ) -> None:
        """Fill the specified area of the wall with bricks."""
        for row in range(bricks_y_start, bricks_y_end):
            for col in range(studs_x_start, studs_x_end):
                p = Piece(
                    colour=self.colour,
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

    def _wall_plane(self)-> Plane3D:
        """Get the wall's plane in world space."""
        wall_origin = self.rotation * Vector(0, 0, 0)  # wall origin, or first brick position if there is a brick at (0, 0)
        stud_to_right = self.rotation * Vector(studs_to_ldu(1), 0, 0)  # 1 stud to where the wall grows in the X direction
        plate_up = self.rotation * Vector(0, plates_to_ldu(1), 0)  # 1 plate height to where the wall grows in the Y direction
        return Plane3D.from_points(p1=wall_origin, p2=stud_to_right, p3=plate_up)

    def insert(self, 
               piece: Piece, 
               at_studs_x: int, 
               at_plates_y: int = -1, 
               at_bricks_y: int = -1,
    ) -> None:
        """Place a piece (e.g. window, door...) and remove bricks to make room for it.

        Removes any fill bricks covered by the inserted piece's footprint, then
        places the piece at the given position.

        Args:
            piece: The Piece object to insert.
            studs_x: Insert position x in studs from the wall's left end.
            plates_y: Insert position y in plates from the wall base.
            bricks_y: Insert position y in brick rows from the wall base (alternative to plates_y).
        """

        at_y_values = (
            at_bricks_y,
            plates_to_brick_height(at_plates_y) if at_plates_y >= 0 else -1,
        )

        _at_bricks_y = single_value_or_error(
            at_y_values,
            non_value=-1,
            param_name="at_y (plates or bricks)",
        )

        _at_plates_y = brick_height_to_plates(_at_bricks_y)

        p_bricks_height: int = plates_to_brick_height(piece.plates_y)

        # avoid removing the upper row due to studs from the piece taking space upwards
        opening_bricks_height = p_bricks_height - 1

        self.opening(at_studs_x=at_studs_x, 
                     studs_width=piece.studs_x,
                     at_bricks_y=_at_bricks_y,
                     bricks_height=opening_bricks_height,
                    )

        p_x = studs_to_ldu(at_studs_x)
        p_y = plates_to_ldu(_at_plates_y)

        # --- place the piece in wall-local coordinates ---
        piece.position = Vector(
            x=p_x,  # place the piece on the studs_x position
            y=p_y,  # place the piece on the plates_y position
            z=0,
        )

        self.add_piece(piece)

        self._insertions.append((at_studs_x, _at_plates_y, piece.studs_x, piece.plates_y))

    def opening(self,
                at_studs_x: int, 
                studs_width: int, 
                at_plates_y: int = -1, 
                plates_height: int = 0, 
                at_bricks_y: int = -1, 
                bricks_height: int = 0) -> None:
        """Create an opening with the given width and height by removing bricks starting at (studs_x, plates_y/bricks_y).

        Args:
            at_studs_x: Opening start position x in studs from the wall's left end.
            studs_width: Opening width in studs.
            at_plates_y: Opening start position y in plates from the wall base.
            plates_height: Opening height in plates from the wall base.
            at_bricks_y: Alternative to at_plates_y, but in brick units.
            bricks_height: Alternative to plates_height, but in brick units.

        """
        # Work in plates units for precision
        at_y_values = (
            at_plates_y,
            brick_height_to_plates(at_bricks_y) if at_bricks_y >= 0 else -1,
        )

        _at_plates_y = single_value_or_error(
            at_y_values,
            non_value=-1,
            param_name="at_y (plates or bricks)",
        )

        height_values = (
            plates_height,
            brick_height_to_plates(bricks_height),
        )

        _plates_height = single_value_or_error(
            height_values,
            non_value=0,
            param_name="height (plates or bricks)",
        )

        _at_bricks_y = plates_to_brick_height(_at_plates_y)
        _bricks_height = plates_to_brick_height(_plates_height)

        # Work in bricks units because of the wall structured around bricks rows
        for row in range(_at_bricks_y, _at_bricks_y + _bricks_height):
            for col in range(at_studs_x, at_studs_x + studs_width):
                p = self._fill.pop((col, row), None)
                if p is not None:
                    self.remove_piece(p)

    def place(self, at: Vector, facing: Literal["north", "south", "east", "west"]) -> None:
        """Place the wall at the given position and facing direction."""
        self.rotation = FACING_ROTATIONS[facing]
        self.position = at

    def place_parallel_to(self, other_wall: Wall, distance_studs: int) -> None:
        """Place this wall parallel to a reference wall at the given distance (in studs).
        
        If distance is positive, this wall will be placed in front of the reference wall, and viceversa.
        Both walls will face the same cardinal direction (north, south, east, or west).
        """
        normal_ldu = studs_to_ldu(distance_studs)
        self.rotation = other_wall.rotation
        self.position = other_wall.position + other_wall.rotation * Vector(0, 0, normal_ldu)
