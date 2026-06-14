"""openings.py — composed Window and Door groups with trim and ornament.

A plain window/door part dropped into a wall reads as a bare hole. These
classes wrap the frame part in a Group together with optional trim and
ornament — a protruding sill, flanking shutters, a flower box — so openings
look designed instead of punched out.

They are placed exactly like a bare part:

    from py4bricks.llm import Window, SANDSTONE
    pal = SANDSTONE
    wall.insert(
        piece=Window(colour=pal.trim, sill_colour=pal.trim, flower_box=True),
        studs_x=6, brick_row=2,
    )

Wall.insert reads `opening_width_studs` / `opening_height_bricks` (exposed
below) to carve a hole sized to the *frame only* — the sill, shutters and
flower box mount on the wall face in front of the opening, so they need no
hole of their own.

Coordinate frame (opening-local): the frame piece sits at the origin, filling
x:[0, frame_width], y:[0, frame_height], z:[0, wall_thickness]. The exterior
wall face is the -Z side, so all ornament protrudes toward -Z.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py4bricks.colour import Colour

from py4bricks.geometry import (
    LDU_PER_BRICK_HEIGHT,
    LDU_PER_STUD,
    LDU_PER_STUD_HEIGHT,
    Identity,
    Matrix,
    Vector,
    YAxis,
    plates_to_ldu,
    studs_to_ldu,
)
from py4bricks.library.colours import Red
from py4bricks.library.parts.doors import (
    Door1X4X6Frame,
    Door1X4X6SmoothWithSquareHandlePlinth,
)
from py4bricks.library.parts.plants import PlantFlower
from py4bricks.library.parts.plates import Plate1X1, Plate1X2
from py4bricks.library.parts.tiles import Tile1X1WithGroove, Tile1X2WithGroove
from py4bricks.library.parts.windows import (
    Window1X2X3Shutter,
    Window1X4X3WithoutShutterTabs,
)
from py4bricks.llm.group import Group
from py4bricks.pieces import CustomPiece, Piece

# How far a sill ledge protrudes from the exterior (-Z) wall face, in LDU.
_PROTRUDE = LDU_PER_STUD / 2

# Mirror across the YZ plane (negate X) — turns a left-handed shutter into its
# right-handed twin so a flanking pair is symmetric.
_REFLECT_X = Matrix([[-1, 0, 0], [0, 1, 0], [0, 0, 1]])


def _opening_height_bricks(frame: Piece) -> int:
    """Brick-row height of the hole a frame needs (same rule as Wall.insert)."""
    return int((frame.ldu_y - LDU_PER_STUD_HEIGHT) // LDU_PER_BRICK_HEIGHT)


def _ledge(width_studs: int, colour: Colour, y: float) -> list[Piece]:
    """A protruding tile ledge `width_studs` wide at height y (sill / step)."""
    pieces: list[Piece] = []
    x = 0
    while x < width_studs:
        use_1x2 = x + 1 < width_studs
        part    = Tile1X2WithGroove if use_1x2 else Tile1X1WithGroove
        tile    = Piece(part=part, colour=colour)
        tile.position = Vector(studs_to_ldu(x), y, -_PROTRUDE)
        pieces.append(tile)
        x += 2 if use_1x2 else 1
    return pieces


class Window(Group):
    """A window frame plus optional sill, shutters and flower box.

    colour       — the window frame colour.
    part         — the window part (default a 4-wide, 3-high frame).
    sill         — add a protruding tile sill under the opening (default True).
    sill_colour  — sill colour (defaults to `colour`).
    shutters     — flank the opening with shutters (default False; their look
                   depends on the part and usually wants visual tuning).
    shutter_colour — shutter colour (defaults to `colour`).
    flower_box   — add a planted box on the sill (default False).
    flower_colour— flower-box plate colour (defaults to `colour`).
    """

    def __init__(
        self,
        *,
        colour: Colour,
        part: str = Window1X4X3WithoutShutterTabs,
        sill: bool = True,
        sill_colour: Colour | None = None,
        shutters: bool = False,
        shutter_colour: Colour | None = None,
        flower_box: bool = False,
        flower_colour: Colour | None = None,
        name: str = "",
    ) -> None:
        super().__init__(name=name)

        frame = Piece(part=part, colour=colour)
        self.add(frame)

        # Hole size for Wall.insert — frame only, not the ornament.
        self.opening_width_studs  = frame.studs_x
        self.opening_height_bricks = _opening_height_bricks(frame)
        self._frame = frame

        if sill:
            for tile in _ledge(frame.studs_x, sill_colour or colour, y=-plates_to_ldu(1)):
                self.add(tile)

        if shutters:
            self._add_shutters(shutter_colour or colour)

        if flower_box:
            self._add_flower_box(flower_colour or colour)

    def _add_shutters(self, colour: Colour) -> None:
        """A mirrored shutter on each side of the frame, flat against the wall face.

        Window1X2X3Shutter is modelled thin along X; a -90° Y turn lays it flat
        (thin in Z). The right shutter additionally reflects across X so the pair
        is symmetric (hinged on opposite edges). Both mount flush — their inner
        face at the wall surface (z=0) — and butt against the frame's side edges.
        """
        flat = Identity().rotate(-90, YAxis)
        left  = CustomPiece(part=Window1X2X3Shutter, colour=colour, transform_by_rotating=flat)
        right = CustomPiece(part=Window1X2X3Shutter, colour=colour, transform_by_rotating=_REFLECT_X * flat)
        mid_y = (self._frame.ldu_y - left.ldu_y) / 2
        left.position  = Vector(-left.ldu_x, mid_y, -left.ldu_z)
        right.position = Vector(self._frame.ldu_x, mid_y, -right.ldu_z)
        self.add(left)
        self.add(right)

    def _add_flower_box(self, colour: Colour) -> None:
        """A small planted box on the exterior face below the opening.

        Plates and flowers mount flush to the wall face (inner edge at z=0) so
        nothing pokes into the interior; flowers are bright on top of the box.
        """
        box_y = -plates_to_ldu(3)
        x = 0
        while x < self._frame.studs_x:
            use_1x2 = x + 1 < self._frame.studs_x
            plate   = Piece(part=Plate1X2 if use_1x2 else Plate1X1, colour=colour)
            plate.position = Vector(studs_to_ldu(x), box_y, -plate.ldu_z)  # flush exterior
            self.add(plate)
            x += 2 if use_1x2 else 1
        # Bright flowers sitting on the box, kept fully on the exterior side.
        for px in range(0, self._frame.studs_x, 2):
            flower = Piece(part=PlantFlower, colour=Red)
            flower.position = Vector(studs_to_ldu(px), box_y + plates_to_ldu(2), -flower.ldu_z)
            self.add(flower)


class Door(Group):
    """A door frame plus optional leaf and a protruding step at the base.

    colour      — the door frame colour.
    part        — the door frame part (default a 4-wide, 6-high frame).
    leaf        — add a door leaf inside the frame (default True).
    leaf_part   — the leaf part.
    leaf_colour — leaf colour (defaults to the accent-like `leaf_colour`, else colour).
    step        — add a protruding tile step at the threshold (default True).
    step_colour — step colour (defaults to `colour`).
    """

    def __init__(
        self,
        *,
        colour: Colour,
        part: str = Door1X4X6Frame,
        leaf: bool = True,
        leaf_part: str = Door1X4X6SmoothWithSquareHandlePlinth,
        leaf_colour: Colour | None = None,
        step: bool = False,
        step_colour: Colour | None = None,
        name: str = "",
    ) -> None:
        super().__init__(name=name)

        frame = Piece(part=part, colour=colour)
        self.add(frame)

        self.opening_width_studs  = frame.studs_x
        self.opening_height_bricks = _opening_height_bricks(frame)
        self._frame = frame

        if leaf:
            door = Piece(part=leaf_part, colour=leaf_colour or colour)
            door.position = Vector(0, 0, 0)
            self.add(door)

        if step:
            for tile in _ledge(frame.studs_x, step_colour or colour, y=-plates_to_ldu(1)):
                self.add(tile)
