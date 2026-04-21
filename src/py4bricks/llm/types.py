"""types.py - Shared compass-direction aliases for the LLM-friendly API.

`Facing` and `Side` both cover the four compass directions, but carry distinct
semantic hints for LLM-generated code:

    Facing — which way an item points (its front face).
             Used by Group.orientation, Wall.facing, place_at(facing=), etc.

    Side   — a compass position relative to another item.
             Used by place_adjacent_to(side=).

Keeping them as separate names lets generated signatures read as templates:

    def make_wall(name: str, facing: Facing) -> Wall: ...
    scene.place_adjacent_to(wall, ref=floor, side="east", facing="north")
"""
from __future__ import annotations

from typing import Literal

Facing = Literal["north", "south", "east", "west"]
Side   = Literal["east", "west", "north", "south"]
