"""walllayout.py — LLM-friendly WallLayout: a turtle-path collection of named Walls.

The turtle starts at the layout origin. Each add_wall() call defines one
*exterior* edge of the perimeter:
  1. Place a Wall at the current turtle corner.
  2. Advance the turtle by the full requested exterior length.

Corner rule
-----------
Consecutive walls are perpendicular and meet at a shared corner stud.
That means:
  * the *path* (the turtle movement) always uses the full exterior length;
  * the *built wall geometry* for every wall after the first is shorter by
    exactly 1 stud, because the previous wall already occupies the corner stud;
  * that shortened wall must also start 1 stud *after* the turtle corner,
    along its travel direction, because the previous wall owns the first stud
    of the new exterior run.

Example:
    south edge: 20 studs exterior  -> build 20 studs starting at corner
    east edge : 15 studs exterior  -> build 14 studs starting 1 stud past corner

This keeps the perimeter dimensions correct while avoiding double-counting
shared corner studs.

Coordinate conventions (layout-local, same as Scene):
    X — east (+) / west (-)
    Z — north (+) / south (-)
    Y — up (plates)

Travel → wall facing:
    "east"  → "north"   (wall extends along world +X)
    "west"  → "south"   (wall extends along world −X)
    "north" → "west"    (wall extends along world +Z)
    "south" → "east"    (wall extends along world −Z)

Usage:
    layout = WallLayout(height_bricks=8, colour=Light_Grey, bonded=True)
    layout.add_wall(name="south", length_studs=20, orientation="east")
    layout.add_wall(name="east",  length_studs=15, orientation="north")
    layout["south"].insert(
        piece=Piece(part=Door1X4X6Frame, colour=Tan),
        studs_x=8, brick_row=0,
    )
    scene.place_at(layout, studs_x=0, plates_y=0, studs_z=0)
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from py4bricks.colour import Colour

from py4bricks.geometry import Vector, orientation_to_rotation, studs_to_ldu
from py4bricks.llm.group import Group
from py4bricks.llm.wall import Wall

# travel orientation → (wall_facing, dx, dz)
#
# dx/dz describe the unit turtle step in layout space for one stud of
# exterior perimeter travel in the chosen direction.
_TRAVEL: dict[str, tuple[str, int, int]] = {
    "east":  ("north", +1,  0),
    "west":  ("south", -1,  0),
    "north": ("west",   0, +1),
    "south": ("east",   0, -1),
}

# Frozensets of the only valid orientation pairs for consecutive walls.
# The layout currently supports a turtle path made of 90° turns only.
_PERPENDICULAR: frozenset[frozenset[str]] = frozenset({
    frozenset({"east",  "north"}),
    frozenset({"east",  "south"}),
    frozenset({"west",  "north"}),
    frozenset({"west",  "south"}),
})


class WallLayout(Group):
    """A turtle-path collection of named, auto-positioned Wall segments.

    Walls must be added in order and each consecutive pair must be
    perpendicular (90°). Callers provide *exterior* wall lengths.

    Internally, the algorithm distinguishes between:
      * exterior path length — how far the turtle advances to the next corner;
      * built wall length — how many studs of wall geometry are created.

    Because adjacent walls share exactly one corner stud, every wall after the
    first is built one stud shorter than its exterior length and is anchored
    one stud forward along its own direction of travel.
    """

    def __init__(
        self,
        *,
        height_bricks: int,
        colour: Colour,
        bonded: bool = False,
    ) -> None:
        super().__init__()
        self._height_bricks      = height_bricks
        self._colour             = colour
        self._bonded             = bonded
        self._walls: dict[str, Wall] = {}

        # Turtle position in layout-stud coordinates. This is the current
        # exterior corner from which the next wall starts.
        self._turtle: tuple[int, int] = (0, 0)

        # Travel direction of the previously added wall, used both for
        # validation and to decide whether the new wall shares a corner.
        self._prev_orientation: str | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_wall(
        self,
        *,
        name: str,
        length_studs: int,
        orientation: Literal["east", "west", "north", "south"],
    ) -> Wall:
        """Add a named Wall and advance the turtle by the exterior length.

        orientation — compass direction the turtle travels to lay this wall.
        length_studs — requested exterior edge length in studs.

        Returns the created Wall so callers can chain .insert() / .opening().

        Raises ValueError if the wall is not perpendicular to the previous one.
        """
        if self._prev_orientation is not None:
            pair = frozenset({self._prev_orientation, orientation})
            if pair not in _PERPENDICULAR:
                raise ValueError(
                    f"Wall '{name}' ('{orientation}') must be perpendicular to "
                    f"previous wall ('{self._prev_orientation}')"
                )

        wall_facing, dx, dz = _TRAVEL[orientation]

        # Current exterior corner.
        cx, cz = self._turtle

        # The first wall owns its whole exterior run and starts exactly at the
        # current turtle corner.
        #
        # Every later wall shares that corner with the previous wall. The
        # previous wall already contributes the first stud of the new exterior
        # run, so the new wall must:
        #   1. be built 1 stud shorter, and
        #   2. start 1 stud forward in its own travel direction.
        shares_corner_with_previous = self._prev_orientation is not None
        built_length = length_studs - 1 if shares_corner_with_previous else length_studs
        start_offset = 1 if shares_corner_with_previous else 0
        wx = cx + dx * start_offset
        wz = cz + dz * start_offset

        if built_length <= 0:
            raise ValueError(
                f"Wall '{name}' exterior length must be at least 2 studs when "
                "it shares a corner with the previous wall"
            )

        wall = Wall(
            width_studs=built_length,
            height_bricks=self._height_bricks,
            colour=self._colour,
            bonded=self._bonded,
        )
        wall.local_pos = Vector(x=studs_to_ldu(wx), y=0, z=studs_to_ldu(wz))
        wall.local_rot = orientation_to_rotation(wall_facing)

        self._walls[name] = wall
        self.children.append(wall)

        # Advance by the full exterior edge length so the turtle lands on the
        # next exterior corner. This is independent of where the shortened wall
        # body starts.
        self._turtle           = (cx + dx * length_studs, cz + dz * length_studs)
        self._prev_orientation = orientation
        return wall

    def __getitem__(self, name: str) -> Wall:
        """Return the named Wall for insert / opening modifications."""
        return self._walls[name]
