"""massing.py — volumes that break the single-box silhouette.

`BayWindow` is a projecting bay you attach to a wall; `House.l_plan` (in
house.py) composes two House blocks into an L. Both fight the "boring box"
problem by adding relief and focal points to the outline.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py4bricks.colour import Colour

from py4bricks.llm.box import Box
from py4bricks.llm.group import Group
from py4bricks.llm.openings import Window
from py4bricks.llm.slab import Slab


class BayWindow(Group):
    """A projecting window bay: a small box jutting from a wall, windows on its
    three outward faces, capped with a flat roof.

    Built projecting toward +Z with its back (the z=0 face) left to sit against
    the host wall — so it attaches exactly like a Balcony, via `facing=<side>`.
    Windows go on the front (and the two sides where they fit); the buried back
    wall is harmless.

    width_studs   — width along the host wall, in studs.
    depth_studs   — how far it projects, in studs.
    height_bricks — bay height in brick rows.
    colour        — wall colour.
    window_colour — window frame colour (defaults to colour).
    cap_colour    — flat-roof colour (defaults to colour).
    """

    def __init__(
        self,
        *,
        width_studs: int,
        depth_studs: int,
        height_bricks: int,
        colour: Colour,
        window_colour: Colour | None = None,
        cap_colour: Colour | None = None,
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        self.width_studs = width_studs
        self.depth_studs = depth_studs
        wc = window_colour or colour

        box = Box(
            width_studs=width_studs, length_studs=depth_studs,
            height_bricks=height_bricks, colour=colour, bonded=True,
            name=f"{name}_box",
        )

        proto = Window(colour=wc)
        win_w, win_h = proto.opening_width_studs, proto.opening_height_bricks
        row = max(1, (height_bricks - win_h) // 2)

        # Outward faces only: front (north, z=depth) and the two sides.
        outward = {
            "north": width_studs - 1,
            "east":  depth_studs - 1,
            "west":  depth_studs - 1,
        }
        for side, wall_width in outward.items():
            if wall_width < win_w or row + win_h > height_bricks:
                continue
            x = (wall_width - win_w) // 2
            box[side].insert(
                piece=Window(colour=wc, sill_colour=wc), studs_x=x, brick_row=row,
            )

        self.add(box)
        cap = Slab(width_studs=width_studs, length_studs=depth_studs, colour=cap_colour or colour)
        self.place_on_top_of(cap, box)
