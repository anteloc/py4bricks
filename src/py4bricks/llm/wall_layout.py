"""wall_layout.py — LLM-friendly WallLayout: a turtle-path collection of named Walls.

The turtle starts at the layout origin. Each add_wall() call:
  1. Places a Wall at the current turtle corner.
  2. Advances the turtle by the full requested length in the travel direction.

This version deliberately keeps the rule simple:
  * every wall is built at exactly the requested length;
  * corners are handled only by placement, not by shortening any wall.

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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py4bricks.colour import Colour
    from py4bricks.llm.types import Facing

from py4bricks.geometry import Vector, orientation_to_rotation, studs_to_ldu
from py4bricks.llm.group import Group
from py4bricks.llm.wall import Wall

# travel orientation → (wall_facing, dx, dz)
# dx/dz are the unit step the turtle takes per stud in that direction.
_TRAVEL: dict[str, tuple[str, int, int]] = {
    "east":  ("north", +1,  0),
    "west":  ("south", -1,  0),
    "north": ("west",   0, +1),
    "south": ("east",   0, -1),
}

# Frozensets of the only valid orientation pairs for consecutive walls.
_PERPENDICULAR: frozenset[frozenset[str]] = frozenset({
    frozenset({"east",  "north"}),
    frozenset({"east",  "south"}),
    frozenset({"west",  "north"}),
    frozenset({"west",  "south"}),
})


class WallLayout(Group):
    """A turtle-path collection of named, auto-positioned Wall segments.

    Walls must be added in order and each consecutive pair must be
    perpendicular (90°). Callers provide the exact wall length to build.

    The algorithm is intentionally simple:
      * place each wall at the current turtle corner;
      * build it at the exact requested length;
      * advance the turtle by that same length to reach the next corner.

    No special shortening or offsetting is applied for shared corners.
    """

    def __init__(
        self,
        *,
        height_bricks: int,
        colour: Colour,
        bonded: bool = False,
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        self._height_bricks      = height_bricks
        self._colour             = colour
        self._bonded             = bonded
        self._walls: dict[str, Wall] = {}
        self._turtle: tuple[int, int] = (0, 0)
        self._prev_orientation: str | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_wall(
        self,
        *,
        name: str,
        length_studs: int,
        direction: Facing,
    ) -> Wall:
        """Add a named Wall and advance the turtle by the same length.

        orientation — compass direction the turtle travels to lay this wall.
        length_studs — exact length to build for this wall.

        Returns the created Wall so callers can chain .insert() / .opening().

        Raises ValueError if the wall is not perpendicular to the previous one.
        """
        if self._prev_orientation is not None:
            pair = frozenset({self._prev_orientation, direction})
            if pair not in _PERPENDICULAR:
                raise ValueError(
                    f"Wall '{name}' ('{direction}') must be perpendicular to "
                    f"previous wall ('{self._prev_orientation}')"
                )

        wall_facing, dx, dz = _TRAVEL[direction]

        # The turtle marks the corner where the next wall begins.
        cx, cz = self._turtle

        # Build the wall exactly as requested, anchored at the current corner.
        wall = Wall(
            width_studs=length_studs,
            height_bricks=self._height_bricks,
            colour=self._colour,
            bonded=self._bonded,
            name=name,
        )
        wall.local_pos = Vector(x=studs_to_ldu(cx), y=0, z=studs_to_ldu(cz))
        wall.local_rot = orientation_to_rotation(wall_facing)

        self._walls[name] = wall
        self.children.append(wall)

        # Move the turtle to the next corner by the same number of studs.
        self._turtle           = (cx + dx * length_studs, cz + dz * length_studs)
        self._prev_orientation = direction
        return wall

    def __getitem__(self, name: str) -> Wall:
        """Return the named Wall for insert / opening modifications."""
        return self._walls[name]
