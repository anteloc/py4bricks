"""group.py - LLM-friendly hierarchical Group for building LEGO structures.

A Group holds Pieces and sub-Groups in its own local coordinate system.
Transforms are composed recursively by Scene at render time — LLM-generated
scripts never perform position arithmetic directly.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from py4bricks.geometry import Identity, Matrix, Vector
from py4bricks.pieces import Piece


@dataclass
class Group:
    """A hierarchical container with a local coordinate system.

    Children can be Piece instances or nested Groups. The Scene walks the tree
    at render time composing transforms level by level:

        world_pos = parent_pos + parent_rot * local_pos
        world_rot = parent_rot * local_rot

    This means rotating or moving a Group automatically transforms all of its
    descendants — no manual coordinate recalculation required.

    Coordinates are in LDU. Use studs_to_ldu / plates_to_ldu from geometry to
    convert from the stud/plate grid when constructing a Group programmatically.
    """

    local_pos: Vector = field(default_factory=lambda: Vector(0, 0, 0))
    local_rot: Matrix = field(default_factory=Identity)
    children: list[Piece | Group] = field(default_factory=list)

    def add(self, item: Piece | Group) -> Group:
        """Add a Piece or sub-Group. Returns self for fluent chaining."""
        self.children.append(item)
        return self
