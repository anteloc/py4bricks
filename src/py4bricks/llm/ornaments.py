"""ornaments.py — small placeable Group ornaments that make buildings lively.

Each class is a self-contained Group built in its own local frame (base at the
origin, growing +X = length, +Y = up, +Z = depth). Drop them into a Scene or
parent Group with the usual verbs:

    from py4bricks.llm import Railing, Chimney, Awning, Lamp, Sign, COTTAGE
    pal = COTTAGE

    scene.place_on_top_of(Railing(length_studs=balcony.studs_x, colour=pal.trim), balcony)
    scene.place_on_top_of(Chimney(height_bricks=5, colour=pal.base), roof, right_studs=2)
    scene.place_adjacent_to(Lamp(), ref=door, side="east")

These compose with the rest of the API (Wall, Box, Roof, Slab, Column …) so an
LLM can sprinkle detail without any geometry math.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py4bricks.colour import Colour
    from py4bricks.llm.types import Facing

from py4bricks.geometry import (
    PLATES_PER_BRICK_HEIGHT,
    Vector,
    orientation_to_rotation,
    plates_to_ldu,
    studs_to_ldu,
)
from py4bricks.library.colours import Dark_Bluish_Grey, Green, Trans_Yellow
from py4bricks.library.parts.bricks import Brick2X2
from py4bricks.library.parts.cones import Cone1X1
from py4bricks.library.parts.plants import PlantFlower
from py4bricks.library.parts.plates import Plate1X1Round, Plate2X2
from py4bricks.library.parts.slopes import SlopeBrick452X1
from py4bricks.library.parts.tiles import (
    Tile1X1WithGroove,
    Tile1X2WithGroove,
    Tile2X2WithGroove,
)
from py4bricks.llm.box import Box
from py4bricks.llm.group import Group
from py4bricks.llm.slab import Slab
from py4bricks.llm.structures import Column
from py4bricks.pieces import Piece

if TYPE_CHECKING:
    from typing import Literal


class Railing(Group):
    """A run of balusters topped by a continuous rail.

    Built on the balustrade pattern from structures.py: a row of Column posts
    capped by a rail. The rail tiles the *full* span (length_studs + 1) with a
    gap-free 1x2 -> 1x1 course — the same rule Slab/coping use — so the last
    post is always covered (unlike a fixed-step tile loop).

    length_studs       — span of the railing, in studs.
    colour             — colour of posts and rail.
    height_bricks      — baluster height (default 2).
    post_spacing_studs — studs between posts (default 2).
    shape              — "round" or "square" balusters (default "round").
    bottom_rail        — add a matching rail at the base, with posts sitting on
                         it (default False).
    """

    def __init__(
        self,
        *,
        length_studs: int,
        colour: Colour,
        height_bricks: int = 2,
        post_spacing_studs: int = 2,
        shape: Literal["round", "square"] = "round",
        bottom_rail: bool = False,
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        self.length_studs = length_studs

        post = Column(
            height_bricks=height_bricks,
            colour=colour,
            shape="circular" if shape == "round" else "square",
        )

        post_base = 1 if bottom_rail else 0
        if bottom_rail:
            self._rail(length_studs + 1, colour, plates_to_ldu(0))

        post_xs = list(range(0, length_studs + 1, post_spacing_studs))
        if post_xs[-1] != length_studs:        # always anchor a post at the far end
            post_xs.append(length_studs)
        for x in post_xs:
            self.place_at(post.copy(), studs_x=x, plates_y=post_base)

        rail_plates = post_base + height_bricks * PLATES_PER_BRICK_HEIGHT
        self._rail(length_studs + 1, colour, plates_to_ldu(rail_plates))

    def _rail(self, span_studs: int, colour: Colour, y: float) -> None:
        """A continuous, gap-free tile rail spanning span_studs at height y."""
        x = 0
        while x < span_studs:
            use_1x2 = x + 1 < span_studs
            part    = Tile1X2WithGroove if use_1x2 else Tile1X1WithGroove
            tile = Piece(part=part, colour=colour)
            tile.position = Vector(studs_to_ldu(x), y, 0)
            self.add(tile)
            x += 2 if use_1x2 else 1


class Chimney(Group):
    """A 2x2 brick stack with a capped pot — place it on a roof.

    place_on_top_of seats anything at the roof's bounding-box top (the ridge
    height), so on a slope a bare chimney floats above the surface. `skirt_bricks`
    extends the stack *downward* below the origin, plunging through the slope so
    the visible top still reads as seated. Placing it near the ridge
    (back_studs/right_studs toward the ridge centre) needs little or no skirt.

    colour        — brick colour.
    height_bricks — visible stack height in bricks (default 4).
    cap_colour    — cap + pot colour (defaults to `colour`).
    skirt_bricks  — hidden bricks added below the base to bridge a slope (default 0).
    """

    def __init__(
        self,
        *,
        colour: Colour,
        height_bricks: int = 4,
        cap_colour: Colour | None = None,
        skirt_bricks: int = 0,
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        self.studs_wide = 2

        # b runs from -skirt_bricks (below the origin) up to the visible top.
        for b in range(-skirt_bricks, height_bricks):
            brick = Piece(part=Brick2X2, colour=colour)
            brick.position = Vector(0, plates_to_ldu(b * PLATES_PER_BRICK_HEIGHT), 0)
            self.add(brick)

        cap_c = cap_colour or colour
        top_y = plates_to_ldu(height_bricks * PLATES_PER_BRICK_HEIGHT)
        cap = Piece(part=Plate2X2, colour=cap_c)
        cap.position = Vector(0, top_y, 0)
        self.add(cap)
        # A single chimney pot, centred on the 2x2 cap (half-stud offsets).
        pot = Piece(part=Cone1X1, colour=cap_c)
        pot.position = Vector(studs_to_ldu(1) / 2, top_y + plates_to_ldu(1), studs_to_ldu(1) / 2)
        self.add(pot)


class Awning(Group):
    """A sloped canopy of 45° slope bricks projecting over a window or door.

    Built as a row of slope bricks along +X; each slope projects 2 studs in
    depth and drops one brick. Face it outward with `facing` to suit the wall.

    width_studs — canopy width, in studs.
    colour      — slope colour.
    facing      — outward direction of the canopy (default "south").
    """

    def __init__(
        self,
        *,
        width_studs: int,
        colour: Colour,
        facing: Facing = "south",
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        self.width_studs = width_studs
        rot = orientation_to_rotation(facing)
        for x in range(width_studs):
            slope = Piece(part=SlopeBrick452X1, colour=colour, rotation=rot)
            slope.position = Vector(studs_to_ldu(x), 0, 0)
            self.add(slope)


class Lamp(Group):
    """A small wall lamp: a round bracket with a glowing cone, to flank a door.

    mount_colour — bracket colour (default dark grey).
    light_colour — lamp colour (default translucent yellow).
    """

    def __init__(
        self,
        *,
        mount_colour: Colour = Dark_Bluish_Grey,
        light_colour: Colour = Trans_Yellow,
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        bracket = Piece(part=Plate1X1Round, colour=mount_colour)
        bracket.position = Vector(0, 0, 0)
        self.add(bracket)
        light = Piece(part=Cone1X1, colour=light_colour)
        light.position = Vector(0, plates_to_ldu(1), 0)
        self.add(light)


class Sign(Group):
    """A small 2x2 tile nameplate, to mount over a door or beside an entrance.

    colour — panel colour.
    """

    def __init__(self, *, colour: Colour, name: str = "") -> None:
        super().__init__(name=name)
        panel = Piece(part=Tile2X2WithGroove, colour=colour)
        panel.position = Vector(0, 0, 0)
        self.add(panel)


class Planter(Group):
    """A low open-top box filled with greenery — anchors façades and balconies.

    Reuses Box for the rim (the well-adjusted closed-perimeter walls) and fills
    the interior with flowers sitting on the rim.

    width_studs / length_studs — footprint, in studs.
    colour        — rim colour.
    height_bricks — rim height (default 2).
    plant_colour  — greenery colour (default green).
    """

    def __init__(
        self,
        *,
        width_studs: int,
        length_studs: int,
        colour: Colour,
        height_bricks: int = 2,
        plant_colour: Colour = Green,
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        self.add(
            Box(width_studs=width_studs, length_studs=length_studs,
                height_bricks=height_bricks, colour=colour)
        )
        top_y = plates_to_ldu(height_bricks * PLATES_PER_BRICK_HEIGHT)
        for x in range(1, width_studs - 1, 2):
            for z in range(1, length_studs - 1, 2):
                flower = Piece(part=PlantFlower, colour=plant_colour)
                flower.position = Vector(studs_to_ldu(x), top_y, studs_to_ldu(z))
                self.add(flower)


class Pergola(Group):
    """Four corner columns under an open egg-crate of beams — an airy canopy.

    Like Porch but with an open slatted top instead of a solid roof: two side
    beams run the length on top of the column rows, and cross rafters span the
    width on top of those at `beam_spacing_studs` intervals.

    width_studs / length_studs — footprint, in studs.
    colour            — column and beam colour.
    height_bricks     — column height (default 6).
    beam_spacing_studs— gap between cross rafters (default 2).
    """

    def __init__(
        self,
        *,
        width_studs: int,
        length_studs: int,
        colour: Colour,
        height_bricks: int = 6,
        beam_spacing_studs: int = 2,
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        post = Column(height_bricks=height_bricks, colour=colour, shape="square")
        for x in (0, width_studs):
            for z in (0, length_studs):
                self.place_at(post.copy(), studs_x=x, studs_z=z)

        beam_y  = plates_to_ldu(height_bricks * PLATES_PER_BRICK_HEIGHT)
        rafter_y = plates_to_ldu(height_bricks * PLATES_PER_BRICK_HEIGHT + 1)
        # two side beams along Z, on the column rows
        for x in (0, width_studs):
            self._tile_line(length_studs + 1, colour, lambda i, x=x: Vector(studs_to_ldu(x), beam_y, studs_to_ldu(i)))
        # cross rafters along X, one plate higher, leaving gaps between them
        for z in range(0, length_studs + 1, beam_spacing_studs):
            self._tile_line(width_studs + 1, colour, lambda i, z=z: Vector(studs_to_ldu(i), rafter_y, studs_to_ldu(z)))

    def _tile_line(self, n_studs: int, colour: Colour, at) -> None:
        """Place n_studs 1x1 tiles, positioned by at(i) — robust, no rotation."""
        for i in range(n_studs):
            tile = Piece(part=Tile1X1WithGroove, colour=colour)
            tile.position = at(i)
            self.add(tile)
