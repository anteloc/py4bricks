"""py4bricks.llm — LLM-friendly API for generating LEGO building models.

Typical imports for generated scripts:

    from py4bricks.llm import Group, Scene, proportional
    from py4bricks.pieces import Piece

Prefer named proportions over magic numbers — they make intent clear and
stay correct when the "whole" changes:

    window_x = proportional(WALL_LENGTH, (1, 3))   # one third of the wall
    mid_y    = proportional(WALL_HEIGHT, (1, 2))   # halfway up

For vertical layout, swap between plates and brick rows:

    brick_height_to_plates(3)   # 3 brick rows = 9 plates
    plates_to_brick_height(9)   # 9 plates = 3 brick rows
"""
from py4bricks.geometry import (
    brick_height_to_plates,
    plates_to_brick_height,
    proportional,
)
from py4bricks.llm.box import Box
from py4bricks.llm.group import Group
from py4bricks.llm.house import House
from py4bricks.llm.massing import BayWindow
from py4bricks.llm.openings import Door, Window
from py4bricks.llm.ornaments import (
    Awning,
    Balcony,
    Chimney,
    Lamp,
    Pergola,
    Planter,
    Railing,
    Sign,
)
from py4bricks.llm.palette import (
    ALL_PALETTES,
    BRICK_RED,
    COTTAGE,
    MODERN,
    SANDSTONE,
    STONE_GREY,
    TUDOR,
    Palette,
)
from py4bricks.llm.roof import Roof
from py4bricks.llm.scene import Scene
from py4bricks.llm.slab import Slab
from py4bricks.llm.structures import Column, Porch
from py4bricks.llm.primitives import BricksRow
from py4bricks.llm.types import Facing, Side
from py4bricks.llm.wall import Wall
from py4bricks.llm.wall_layout import WallLayout

__all__ = [
    "ALL_PALETTES",
    "BRICK_RED",
    "COTTAGE",
    "MODERN",
    "SANDSTONE",
    "STONE_GREY",
    "TUDOR",
    "Awning",
    "Balcony",
    "BayWindow",
    "Box",
    "BricksRow",
    "Chimney",
    "Column",
    "Door",
    "Facing",
    "Group",
    "House",
    "Lamp",
    "Palette",
    "Pergola",
    "Planter",
    "Porch",
    "Railing",
    "Sign",
    "Window",
    "Roof",
    "Scene",
    "Side",
    "Slab",
    "Wall",
    "WallLayout",
    "brick_height_to_plates",
    "plates_to_brick_height",
    "proportional",
]
