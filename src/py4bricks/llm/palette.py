"""palette.py — curated colour schemes for good-looking buildings.

LLMs are weak at picking harmonious colours. A Palette bundles a coordinated
set of roles so generated scripts choose a named scheme and read colours by
intent instead of guessing:

    from py4bricks.llm import Palette, SANDSTONE

    pal = SANDSTONE
    box  = Box(width_studs=20, length_studs=15, height_bricks=8, colour=pal.wall)
    box["south"].foundation(colour=pal.base)
    box["south"].coping(colour=pal.trim)

Roles:
    wall   — the main field colour of the walls
    trim   — frames, sills, coping, string courses (contrasts the wall)
    accent — shutters, doors, small focal details
    roof   — roof slopes and ridge
    base   — foundation course and ground (anchors the build visually)
    glass  — transparent window panes
"""
from __future__ import annotations

from dataclasses import dataclass

from py4bricks.colour import Colour
from py4bricks.library.colours import (
    Black,
    Brown,
    Dark_Blue,
    Dark_Bluish_Grey,
    Dark_Brown,
    Dark_Green,
    Dark_Red,
    Dark_Tan,
    Light_Bluish_Grey,
    Reddish_Brown,
    Tan,
    Trans_Clear,
    Trans_Light_Blue,
    White,
)


@dataclass(frozen=True)
class Palette:
    """A coordinated set of colours keyed by architectural role."""

    wall: Colour
    trim: Colour
    accent: Colour
    roof: Colour
    base: Colour
    glass: Colour


# Curated presets — each is a tested, harmonious combination.
SANDSTONE = Palette(
    wall=Tan, trim=White, accent=Dark_Red, roof=Dark_Red, base=Dark_Tan, glass=Trans_Light_Blue,
)
BRICK_RED = Palette(
    wall=Reddish_Brown, trim=Tan, accent=Dark_Green, roof=Dark_Bluish_Grey, base=Dark_Bluish_Grey, glass=Trans_Clear,
)
COTTAGE = Palette(
    wall=White, trim=Brown, accent=Dark_Green, roof=Dark_Red, base=Dark_Bluish_Grey, glass=Trans_Light_Blue,
)
STONE_GREY = Palette(
    wall=Light_Bluish_Grey, trim=White, accent=Dark_Blue, roof=Dark_Bluish_Grey, base=Dark_Bluish_Grey, glass=Trans_Light_Blue,
)
MODERN = Palette(
    wall=White, trim=Light_Bluish_Grey, accent=Black, roof=Light_Bluish_Grey, base=Dark_Bluish_Grey, glass=Trans_Light_Blue,
)
TUDOR = Palette(
    wall=White, trim=Dark_Brown, accent=Dark_Brown, roof=Dark_Red, base=Dark_Bluish_Grey, glass=Trans_Clear,
)

ALL_PALETTES: dict[str, Palette] = {
    "sandstone": SANDSTONE,
    "brick_red": BRICK_RED,
    "cottage": COTTAGE,
    "stone_grey": STONE_GREY,
    "modern": MODERN,
    "tudor": TUDOR,
}
