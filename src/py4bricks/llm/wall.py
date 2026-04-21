"""wall.py — LLM-friendly Wall, a Group subclass with lazy piece building.

A Wall is a non-bonded rectangular surface of Brick1X2/Brick1X1 pieces that
extends Group so the Scene can place, rotate, and stack it exactly like any
other Group — no add_to_scene() indirection needed.

Coordinate conventions (wall-local):
    studs_x   — horizontal along the wall face, 0 = left end
    brick_row — vertical from wall base, 0 = bottom row

Typical usage:
    wall = Wall(width_studs=40, height_bricks=35, colour=Light_Grey)
    wall.insert(piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
                studs_x=8, brick_row=16)
    scene.place_at(wall, studs_x=0, plates_y=0, studs_z=0, facing="north")
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py4bricks.colour import Colour
    from py4bricks.llm.types import Facing

from py4bricks.geometry import (
    LDU_PER_BRICK_HEIGHT,
    LDU_PER_STUD_HEIGHT,
    PLATES_PER_BRICK_HEIGHT,
    Vector,
    plates_to_ldu,
    studs_to_ldu,
)
from py4bricks.library.parts.bricks import Brick1X1, Brick1X2
from py4bricks.llm.group import Group
from py4bricks.pieces import Piece


class Wall(Group):
    """A non-bonded rectangular wall of Brick1X2/Brick1X1 pieces.

    Extends Group: the Scene can place, rotate, and query it like any other
    Group. Children (the actual brick Pieces) are built lazily from the
    internal boolean grid and only materialised when the Scene first
    traverses the Wall (at render or query time).

    grid[stud_x][plate_y]: True = solid brick, False = open space.

    When bonded=True, odd brick rows are shifted 1 stud right (running bond):
    a Brick1X1 filler is placed at stud 0, then Brick1X2 pairs follow from
    stud 1, so vertical joints never align between adjacent rows.
    """

    def __init__(
        self,
        *,
        width_studs: int,
        height_bricks: int,
        colour: Colour,
        facing: Facing = "north",
        bonded: bool = False,
        name: str = "",
    ) -> None:
        # Initialise Group at the local origin with the given default facing.
        # The dataclass __init__ will call children.setter with [] via __post_init__.
        super().__init__(name=name, orientation=facing)

        self._width_studs   = width_studs
        self._height_bricks = height_bricks
        self._colour        = colour
        self._bonded        = bonded
        self._height_plates = height_bricks * PLATES_PER_BRICK_HEIGHT

        # grid[stud_x][plate_y]: True = solid, False = open
        self._grid: list[list[bool]] = [
            [True] * self._height_plates
            for _ in range(width_studs)
        ]
        # (piece, wall-local studs_x, wall-local brick_row)
        self._inserts: list[tuple[Piece, int, int]] = []
        self._dirty = True  # trigger build on first children access

    # ------------------------------------------------------------------
    # children property — overrides the dataclass field from Group
    # ------------------------------------------------------------------

    @property  # type: ignore[override]
    def children(self) -> list[Piece | Group]:
        """Lazily rebuild piece list from grid when dirty, then return it."""
        if self._dirty:
            self._build()
            self._dirty = False
        return self._children

    @children.setter
    def children(self, value: list) -> None:
        # Intercepts Group dataclass setting self.children = [] at __init__ time.
        self._children: list[Piece | Group] = value

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def opening(
        self,
        *,
        studs_x: int,
        brick_row: int,
        width_studs: int,
        height_bricks: int,
    ) -> None:
        """Carve a rectangular opening in the wall.

        studs_x       — left edge in studs from the wall's left end
        brick_row     — bottom row in brick rows from the wall base
        width_studs   — opening width in studs
        height_bricks — opening height in brick rows
        """
        plate_start = brick_row   * PLATES_PER_BRICK_HEIGHT
        plate_end   = plate_start + height_bricks * PLATES_PER_BRICK_HEIGHT
        for x in range(studs_x, studs_x + width_studs):
            for y in range(plate_start, plate_end):
                self._grid[x][y] = False
        self._dirty = True

    def insert(
        self,
        *,
        piece: Piece,
        studs_x: int,
        brick_row: int,
    ) -> None:
        """Carve an opening sized to piece and schedule piece for placement.

        Opening dimensions are derived automatically:
            width_studs   = piece.studs_x
            height_bricks = (piece.ldu_y - LDU_PER_STUD_HEIGHT) / LDU_PER_BRICK_HEIGHT
        This is an exact integer for all standard window and door frame parts.

        studs_x   — left edge in studs from the wall's left end
        brick_row — bottom row in brick rows from the wall base
        """
        width_studs   = piece.studs_x
        height_bricks = int(
            (piece.ldu_y - LDU_PER_STUD_HEIGHT) // LDU_PER_BRICK_HEIGHT,
        )
        self.opening(
            studs_x=studs_x, brick_row=brick_row,
            width_studs=width_studs, height_bricks=height_bricks,
        )
        self._inserts.append((piece, studs_x, brick_row))
        # _dirty already set by opening()

    # ------------------------------------------------------------------
    # Internal build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        """Rebuild _children from the grid and scheduled inserts.

        All Pieces live directly in the Wall's local space with explicit
        positions — no row sub-Groups required.
        """
        self._children.clear()

        for brick_row in range(self._height_bricks):
            plate_y     = brick_row * PLATES_PER_BRICK_HEIGHT
            # bond_offset drives the phase: Brick1X2 may only start at studs
            # where x % 2 == bond_offset.  This keeps joints offset from even
            # rows everywhere — including to the right of openings, where a
            # naive greedy scan would otherwise reset the phase.
            bond_offset = 1 if (self._bonded and brick_row % 2 == 1) else 0

            x = 0
            while x < self._width_studs:
                if not self._grid[x][plate_y]:
                    x += 1
                    continue
                use_1x2 = (
                    x % 2 == bond_offset
                    and x + 1 < self._width_studs
                    and self._grid[x + 1][plate_y]
                )
                part  = Brick1X2 if use_1x2 else Brick1X1
                brick = Piece(part=part, colour=self._colour)
                brick.position = Vector(
                    studs_to_ldu(x),
                    plates_to_ldu(plate_y),
                    0,
                )
                self._children.append(brick)
                x += 2 if use_1x2 else 1

        for piece, ins_studs_x, ins_brick_row in self._inserts:
            piece.position = Vector(
                studs_to_ldu(ins_studs_x),
                plates_to_ldu(ins_brick_row * PLATES_PER_BRICK_HEIGHT),
                0,
            )
            self._children.append(piece)
