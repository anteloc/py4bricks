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

import random
from typing import TYPE_CHECKING, cast, Literal

if TYPE_CHECKING:
    from py4bricks.colour import Colour
    from py4bricks.llm.types import Facing

from py4bricks.geometry import (
    LDU_PER_BRICK_HEIGHT,
    LDU_PER_STUD_HEIGHT,
    PLATES_PER_BRICK_HEIGHT,
    Vector,
    ldu_to_studs,
    orientation_to_rotation,
    plates_to_ldu,
    studs_to_ldu, Identity, YAxis,
)
from py4bricks.library.parts.bricks import Brick1X1, Brick1X2, Brick2X2, Brick2X4
from py4bricks.library.parts.tiles import Tile1X1WithGroove, Tile1X2WithGroove
from py4bricks.llm.group import Group
from py4bricks.pieces import Piece, CustomPiece



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

    @classmethod
    def parallel_wall(
        cls,
        *,
        name: str,
        to_wall: Wall,
        at_distance_studs: int,
        colour: Colour | None = None,
    ) -> Wall:
        """Build a copy of to_wall, offset perpendicular to its run.

        The new wall keeps to_wall's facing, length, height, and thickness; it
        is shifted by at_distance_studs along to_wall's local +Z (the axis
        perpendicular to the wall's run), so it stays parallel for any facing.

        name              — name for the new wall.
        to_wall           — the existing wall to copy and offset from.
        at_distance_studs — perpendicular distance from to_wall, in studs.
        colour            — override colour; None keeps to_wall's colour.
        """
        wall = to_wall.copy()

        wall.name = name
        wall._colour = colour if colour is not None else to_wall._colour

        # The wall extends along its local +X axis, so its local +Z axis is
        # perpendicular to the wall's run. Rotating that local offset through
        # to_wall.local_rot lands it on the correct world axis for any facing.
        pos_offset = to_wall.local_rot * Vector(0, 0, studs_to_ldu(at_distance_studs))
        wall.position = to_wall.position + pos_offset

        return wall

    @classmethod
    def divider_wall(
        cls,
        *,
        from_wall: Wall,
        at_width_studs: int,
        to_parallel_wall: Wall,
        colour: Colour | None = None,
        bonded: bool = False,
    ) -> Wall:
        """A wall perpendicular to from_wall, starting at_studs_x on from_wall,
        that extends to to_parallel_wall, effectively dividing the corridor between from_wall and to_parallel_wall.
        """
        # Express to_parallel_wall's offset in from_wall's local frame.
        # Local +X is along from_wall's run; local +Z is the perpendicular
        # axis the divider must span. Working in local space makes the rest
        # of this method orientation-agnostic.
        world_delta = to_parallel_wall.position - from_wall.position
        local_delta = from_wall.local_rot.transpose() * world_delta

        distance_studs = ldu_to_studs(abs(local_delta.z)) - 1

        x_offset_studs = at_width_studs - 1
        z_offset_studs = 1 if local_delta.z > 0 else -1

        # at_width_studs lives along from_wall's local +X; the +1 z nudge
        # avoids interpenetration with from_wall. Rotate the local offset
        # through from_wall.local_rot to land in world coordinates.
        world_offset = from_wall.local_rot * Vector(
            studs_to_ldu(x_offset_studs), 0, studs_to_ldu(z_offset_studs))
        wall_pos = from_wall.position + world_offset

        # The divider's local +X must point along from_wall's local ±Z, so
        # its rotation is from_wall.local_rot composed with a Y spin: 270°
        # ("west") sends local +X to local +Z, 90° ("east") to local -Z.
        spin: Facing = "west" if local_delta.z > 0 else "east"
        divider_rot = from_wall.local_rot * orientation_to_rotation(spin)

        wall = cls(
            name=f"{from_wall.name}_to_{to_parallel_wall.name}_divider",
            width_studs=distance_studs,
            height_bricks=from_wall._height_bricks,
            colour=colour if colour is not None else from_wall._colour,
            bonded=bonded,
            thickness=from_wall._thickness,
        )

        wall.position = wall_pos
        wall.local_rot = divider_rot
        return wall

    def __init__(
        self,
        *,
        width_studs: int,
        height_bricks: int,
        colour: Colour,
        facing: Facing = "north",
        bonded: bool = False,
        name: str = "",
        thickness: Literal["thick", "thin"] = "thin",
    ) -> None:
        # Initialise Group at the local origin with the given default facing.
        # The dataclass __init__ will call children.setter with [] via __post_init__.
        super().__init__(name=name, orientation=facing)

        self._width_studs   = width_studs
        self._height_bricks = height_bricks
        self._colour        = colour
        self._bonded        = bonded
        self._thickness     = thickness
        self._height_plates = height_bricks * PLATES_PER_BRICK_HEIGHT

        match thickness:
            case "thin":
                self._small_brick  = Piece(part=Brick1X1, colour=colour)
                self._mid_brick:   Piece | None = None
                self._medium_brick = Piece(part=Brick1X2, colour=colour)
                self._medium_width = 2
                self.thickness_studs = 1
            case "thick":
                # _small_brick: rotated Brick1X2 ≡ Brick2X1 (1 stud wide, 2 studs deep)
                self._small_brick  = CustomPiece(
                    part=Brick1X2, colour=colour,
                    transform_by_rotating=Identity().rotate(-90, YAxis),
                )
                self._mid_brick    = Piece(part=Brick2X2, colour=colour)  # 2w x 2d
                self._medium_brick = Piece(part=Brick2X4, colour=colour)  # 4w x 2d
                self._medium_width = 4
                self.thickness_studs = 2
        # grid[stud_x][plate_y]: True = solid, False = open
        self._grid: list[list[bool]] = [
            [True] * self._height_plates
            for _ in range(width_studs)
        ]
        # (piece, wall-local studs_x, wall-local brick_row)
        self._inserts: list[tuple[Piece, int, int]] = []

        # Surface enrichment (all opt-in; default keeps the plain wall look).
        self._foundation_rows   = 0
        self._foundation_colour: Colour | None = None
        self._bands: dict[int, Colour]         = {}        # brick_row -> colour
        self._mottle: tuple[Colour, float, int] | None = None  # (colour, ratio, seed)
        self._coping_colour: Colour | None     = None

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
        piece: Piece | Group,
        studs_x: int,
        brick_row: int,
    ) -> None:
        """Carve an opening sized to piece and schedule piece for placement.

        Accepts either a bare part Piece or a composed opening (Window/Door).
        For a composed opening the hole is sized to its `opening_width_studs` /
        `opening_height_bricks` (the frame only) so the sill, shutters and
        flower box mount on the wall face without needing a hole.

        For a bare Piece the dimensions are derived automatically:
            width_studs   = piece.studs_x
            height_bricks = (piece.ldu_y - LDU_PER_STUD_HEIGHT) / LDU_PER_BRICK_HEIGHT
        This is an exact integer for all standard window and door frame parts.

        studs_x   — left edge in studs from the wall's left end
        brick_row — bottom row in brick rows from the wall base
        """
        width_studs = getattr(piece, "opening_width_studs", None) or piece.studs_x
        height_bricks = getattr(piece, "opening_height_bricks", None) or int(
            (piece.ldu_y - LDU_PER_STUD_HEIGHT) // LDU_PER_BRICK_HEIGHT,
        )
        self.opening(
            studs_x=studs_x, brick_row=brick_row,
            width_studs=width_studs, height_bricks=height_bricks,
        )
        self._inserts.append((piece, studs_x, brick_row))
        # _dirty already set by opening()

    # ------------------------------------------------------------------
    # Surface enrichment — opt-in, chainable, applied at build time
    # ------------------------------------------------------------------

    def foundation(self, *, colour: Colour, brick_rows: int = 1) -> Wall:
        """Recolour the bottom `brick_rows` rows to read as a foundation/plinth."""
        self._foundation_rows  = brick_rows
        self._foundation_colour = colour
        self._dirty = True
        return self

    def band(self, *, brick_row: int, colour: Colour) -> Wall:
        """Recolour a single course to a contrasting string course."""
        self._bands[brick_row] = colour
        self._dirty = True
        return self

    def mottle(self, *, colour: Colour, ratio: float = 0.12, seed: int = 0) -> Wall:
        """Scatter `ratio` of the plain wall bricks into `colour` for masonry texture.

        Deterministic per cell (same seed → same pattern). Foundation and band
        courses are left untouched so they stay clean and legible.
        """
        self._mottle = (colour, ratio, seed)
        self._dirty = True
        return self

    def coping(self, *, colour: Colour) -> Wall:
        """Cap the wall top with a smooth tile course, so it doesn't end in raw studs."""
        self._coping_colour = colour
        self._dirty = True
        return self

    def copy(self) -> Wall:
        """Create a deep copy of this Wall, including all inserts but excluding children."""
        new_wall = Wall(
            width_studs=self._width_studs,
            height_bricks=self._height_bricks,
            colour=self._colour,
            bonded=self._bonded,
            thickness=self._thickness,
            name=f"{self.name}_copy",
        )
        new_wall._grid = [row.copy() for row in self._grid]
        new_wall._inserts = self._inserts.copy()
        # Carry surface enrichment so copies (parallel/divider walls) match.
        new_wall._foundation_rows   = self._foundation_rows
        new_wall._foundation_colour = self._foundation_colour
        new_wall._bands             = dict(self._bands)
        new_wall._mottle            = self._mottle
        new_wall._coping_colour     = self._coping_colour
        # `orientation` is stale once Scene.place_at has run, so copy the
        # actual rotation matrix instead of going through the facing string.
        new_wall.local_rot = self.local_rot.copy()
        new_wall._dirty = True
        return new_wall

    # ------------------------------------------------------------------
    # Internal build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        """Rebuild _children from the grid, enrichment, and scheduled inserts."""
        self._children.clear()
        for brick_row in range(self._height_bricks):
            self._children.extend(self._bricks_for_row(brick_row))
        if self._coping_colour is not None:
            self._children.extend(self._coping_pieces())
        self._place_inserts()

    def _colour_for(self, brick_row: int, x: int) -> Colour:
        """Resolve a cell's colour from the enrichment rules.

        Precedence: explicit band course > foundation > scattered mottle > wall.
        Bands/foundation win so deliberate courses stay clean; mottle only
        textures the plain field.
        """
        if brick_row in self._bands:
            return self._bands[brick_row]
        if brick_row < self._foundation_rows and self._foundation_colour is not None:
            return self._foundation_colour
        if self._mottle is not None:
            colour, ratio, seed = self._mottle
            if random.Random(f"{seed}:{x}:{brick_row}").random() < ratio:
                return colour
        return self._colour

    def _coping_pieces(self) -> list[Piece]:
        """A smooth tile course capping the wall top, covering its full thickness."""
        pieces: list[Piece] = []
        y = plates_to_ldu(self._height_plates)
        for z in range(self.thickness_studs):
            x = 0
            while x < self._width_studs:
                use_1x2 = x + 1 < self._width_studs
                part    = Tile1X2WithGroove if use_1x2 else Tile1X1WithGroove
                tile    = Piece(part=part, colour=cast("Colour", self._coping_colour))
                tile.position = Vector(studs_to_ldu(x), y, studs_to_ldu(z))
                pieces.append(tile)
                x += 2 if use_1x2 else 1
        return pieces

    def _bricks_for_row(self, brick_row: int) -> list[Piece]:
        """Return the brick Pieces that fill one horizontal row of the grid."""
        plate_y = brick_row * PLATES_PER_BRICK_HEIGHT
        # Odd rows shift by half a medium brick so vertical joints never align.
        bond_offset = (
            self._medium_width // 2 if (self._bonded and brick_row % 2 == 1) else 0
        )

        pieces: list[Piece] = []
        x = 0
        while x < self._width_studs:
            if not self._grid[x][plate_y]:
                x += 1
                continue
            brick, step = self._choose_brick(x, plate_y, bond_offset)
            brick.colour = self._colour_for(brick_row, x)
            brick.position = Vector(studs_to_ldu(x), plates_to_ldu(plate_y), 0)
            pieces.append(brick)
            x += step
        return pieces

    def _choose_brick(
        self, x: int, plate_y: int, bond_offset: int,
    ) -> tuple[Piece, int]:
        """Return (brick_copy, step) for the solid cell at (x, plate_y).

        studs_to_align: studs needed to reach the next bond-aligned position.
        mid fires at studs_to_align ∈ {0, 2}; small fires for 1 and 3 so that
        alignment-restoring smalls always land flush at opening edges.
        """
        studs_to_align = (bond_offset - x) % self._medium_width

        fits_medium = (
            studs_to_align == 0
            and x + self._medium_width <= self._width_studs
            and all(self._grid[x + i][plate_y] for i in range(1, self._medium_width))
        )
        # Use mid in exactly two situations:
        #  studs_to_align == 0: aligned, but medium can't fit (opening or wall end
        #                       cuts it short) — mid is the largest brick that fits.
        #  studs_to_align == 2: mid is the exact filler to reach the next alignment.
        # studs_to_align == 3 must fall to small first so the small lands flush
        # against the opening edge, not 2 studs inside the run.
        fits_mid = (
            not fits_medium
            and studs_to_align in (0, 2)
            and self._mid_brick is not None
            and x + 2 <= self._width_studs
            and self._grid[x + 1][plate_y]
        )

        if fits_medium:
            return self._medium_brick.copy(), self._medium_width
        if fits_mid:
            return cast("Piece", self._mid_brick).copy(), 2
        return self._small_brick.copy(), 1

    def _place_inserts(self) -> None:
        """Position and append all scheduled insert pieces."""
        for piece, studs_x, brick_row in self._inserts:
            piece.position = Vector(
                studs_to_ldu(studs_x),
                plates_to_ldu(brick_row * PLATES_PER_BRICK_HEIGHT),
                plates_to_ldu(self.thickness_studs - 1),
            )
            self._children.append(piece)
