"""group.py - LLM-friendly hierarchical Group for building LEGO structures.

A Group holds Pieces and sub-Groups in its own local coordinate system.
Transforms are composed recursively by Scene at render time — LLM-generated
scripts never perform position arithmetic or unit conversions directly.
"""
from __future__ import annotations

from dataclasses import dataclass, field, InitVar
from typing import Literal

from py4bricks.geometry import (
    Matrix,
    Vector,
    orientation_to_rotation,
    plates_to_ldu,
    studs_to_ldu,
)
from py4bricks.pieces import Piece


@dataclass
class Group:
    """A hierarchical container with a local coordinate system.

    Position is given in studs (X/Z) and plates (Y); orientation as a compass
    direction. The Group converts these to internal Vector/Matrix on construction,
    so LLM-generated scripts stay free of numeric conversions.

    Children can be Piece instances or nested Groups. The Scene walks the tree
    at render time composing transforms level by level:

        world_pos = parent_pos + parent_rot * local_pos
        world_rot = parent_rot * local_rot

    Rotating or moving a Group automatically transforms all of its descendants.
    """

    studs_x:     InitVar[int] = 0
    plates_y:    InitVar[int] = 0
    studs_z:     InitVar[int] = 0
    orientation: InitVar[Literal["north", "south", "east", "west"]] = "north"
    children:    list[Piece | Group] = field(default_factory=list)

    # Derived from init vars in __post_init__; used by Scene._resolve()
    local_pos: Vector = field(init=False)
    local_rot: Matrix = field(init=False)

    def __post_init__(
        self,
        studs_x: int,
        plates_y: int,
        studs_z: int,
        orientation: Literal["north", "south", "east", "west"],
    ) -> None:
        self.local_pos = Vector(
            x=studs_to_ldu(studs_x),
            y=plates_to_ldu(plates_y),
            z=studs_to_ldu(studs_z),
        )
        self.local_rot = orientation_to_rotation(orientation)

    def add(self, item: Piece | Group) -> Group:
        """Add a Piece or sub-Group. Returns self for fluent chaining."""
        self.children.append(item)
        return self
