"""box.py — LLM-friendly Box: a closed rectangular WallLayout with 4 named walls.

A Box automatically lays out four walls forming a closed perimeter:

    south → east → north → west

Coordinate conventions (same as WallLayout/Scene):
    X — east (+) / west (-)
    Z — north (+) / south (-)
    Y — up (plates)

Wall assignment:
    "south"  travels east,  length = width_studs   (faces east/outward south)
    "east"   travels north, length = length_studs  (faces west/outward east)
    "north"  travels west,  length = width_studs   (faces west/outward north)
    "west"   travels south, length = length_studs  (faces east/outward west)

Corners follow the same no-shortening rule as WallLayout: each wall is built
at the exact requested length and the turtle advances by the same amount.

Usage:
    box = Box(width_studs=20, length_studs=15, height_bricks=8,
              colour=Light_Grey, bonded=True)
    box["south"].insert(piece=Piece(part=Door1X4X6Frame, colour=Tan),
                        studs_x=8, brick_row=0)
    scene.place_at(box, studs_x=0, plates_y=0, studs_z=0)
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py4bricks.colour import Colour

from py4bricks.llm.wall_layout import WallLayout


class Box(WallLayout):
    """A closed rectangular perimeter of exactly 4 named walls.

    Walls are added automatically in order: south → east → north → west.
    Use box["south"], box["east"], box["north"], box["west"] to access
    individual walls for inserts and openings.
    """

    def __init__(
        self,
        *,
        width_studs: int,
        length_studs: int,
        height_bricks: int,
        colour: Colour,
        bonded: bool = False,
    ) -> None:
        super().__init__(height_bricks=height_bricks, colour=colour, bonded=bonded)

        self.width_studs  = width_studs
        self.length_studs = length_studs

        self.add_wall(name="south", length_studs=width_studs - 1,  orientation="east")
        self.add_wall(name="east",  length_studs=length_studs - 1, orientation="north")
        self.add_wall(name="north", length_studs=width_studs - 1,  orientation="west")
        self.add_wall(name="west",  length_studs=length_studs - 1, orientation="south")
