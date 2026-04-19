"""scene.py - LLM-friendly Scene: the root of the render tree.

The Scene owns the top-level list of Pieces and Groups. At render time it
walks the tree recursively, composing transforms level by level, and emits
a flat stream of LDraw type-1 lines via Piece.render().

Coordinate conventions (same as geometry.py):
    X — horizontal, positive to the right    (studs)
    Y — vertical,   positive upward          (plates)
    Z — depth,      positive towards the back (studs)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from py4bricks.geometry import (
    Identity,
    LDU_PER_STUD_HEIGHT,
    Matrix,
    Vector,
    orientation_to_rotation,
    plates_to_ldu,
    studs_to_ldu,
)
from py4bricks.llm.group import Group
from py4bricks.pieces import Piece

if TYPE_CHECKING:
    from collections.abc import Iterator

# Tolerance for piece_at() position matching (half an LDU — smaller than any grid step)
_POSITION_TOLERANCE: float = 0.5

_ORIGIN:   Vector = Vector(0, 0, 0)
_IDENTITY: Matrix = Identity()


@dataclass
class _Bounds:
    """Axis-aligned bounding box in world space, accumulated during tree traversal."""

    min_x: float = field(default_factory=lambda: float("inf"))
    max_x: float = field(default_factory=lambda: float("-inf"))
    min_y: float = field(default_factory=lambda: float("inf"))
    max_y: float = field(default_factory=lambda: float("-inf"))
    min_z: float = field(default_factory=lambda: float("inf"))
    max_z: float = field(default_factory=lambda: float("-inf"))

    def expand(self, pt: Vector) -> None:
        self.min_x = min(self.min_x, pt.x)
        self.max_x = max(self.max_x, pt.x)
        self.min_y = min(self.min_y, pt.y)
        self.max_y = max(self.max_y, pt.y)
        self.min_z = min(self.min_z, pt.z)
        self.max_z = max(self.max_z, pt.z)


class Scene:
    """Root container for all Pieces and Groups in a model.

    Rendering resolves the full Group transform chain lazily: structures can be
    repositioned or rotated after construction, and the output is always correct.
    """

    def __init__(self) -> None:
        self.children: list[Piece | Group] = []

        # Duck-typed position/rotation so Piece.__repr__ works when piece.group = scene.
        self.position: Vector = Vector(0, 0, 0)
        self.rotation: Matrix = Identity()

    # ------------------------------------------------------------------
    # Public placement API
    # ------------------------------------------------------------------

    def place(
        self,
        item: Piece | Group,
        *,
        facing: Literal["north", "south", "east", "west"] = "north",
    ) -> Piece | Group:
        """Add item to the scene with the given orientation.

        Use when item's pieces are already positioned within it (e.g. a Group row).
        """
        self._set_facing(item, facing)
        self._register(item)
        return item

    def place_at(
        self,
        piece: Piece,
        *,
        studs_x: int,
        plates_y: int,
        studs_z: int,
        facing: Literal["north", "south", "east", "west"] = "north",
    ) -> Piece:
        """Place a single Piece at absolute grid coordinates and add it to the scene."""
        Piece.place_at(
            piece=piece,
            studs_x=studs_x,
            plates_y=plates_y,
            studs_z=studs_z,
            orientation=facing,
        )
        self._register(piece)
        return piece

    def place_on_top_of(
        self,
        item: Piece | Group,
        ref: Piece | Group,
        *,
        right_studs: int = 0,
        back_studs: int = 0,
        facing: Literal["north", "south", "east", "west"] = "north",
    ) -> Piece | Group:
        """Stack item flush on top of ref, optionally offset by studs.

        right_studs — shift item to the right (positive X) by this many studs.
        back_studs  — shift item towards the back (positive Z) by this many studs.
        """
        ref_bounds     = self._bounds(ref, _ORIGIN, _IDENTITY)
        structural_top = ref_bounds.max_y - LDU_PER_STUD_HEIGHT
        item.position  = Vector(
            ref.position.x + studs_to_ldu(right_studs),
            structural_top,
            ref.position.z + studs_to_ldu(back_studs),
        )
        self._set_facing(item, facing)
        self._register(item)
        return item

    def place_adjacent_to(
        self,
        item: Piece | Group,
        ref: Piece | Group,
        *,
        side: Literal["east", "west", "north", "south"],
        facing: Literal["north", "south", "east", "west"] = "north",
    ) -> Piece | Group:
        """Place item flush against ref on the given compass side."""
        self._place_adjacent(item, ref=ref, side=side)
        self._set_facing(item, facing)
        self._register(item)
        return item

    def piece_at(self, studs_x: int, plates_y: int, studs_z: int) -> Piece | None:
        """Return the first Piece whose world-space origin matches the given grid position."""
        target = Vector(
            studs_to_ldu(studs_x), plates_to_ldu(plates_y), studs_to_ldu(studs_z),
        )

        def _near(v: Vector) -> bool:
            return (abs(v.x - target.x) < _POSITION_TOLERANCE
                    and abs(v.y - target.y) < _POSITION_TOLERANCE
                    and abs(v.z - target.z) < _POSITION_TOLERANCE)

        return next(
            (
                piece
                for item in self.children
                for piece, world_pos, _ in self._traverse(item, _ORIGIN, _IDENTITY)
                if _near(world_pos)
            ),
            None,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _register(self, item: Piece | Group) -> None:
        """Append item to the scene tree; duck-type Piece.group for __repr__ compat."""
        self.children.append(item)
        if isinstance(item, Piece):
            item.group = self  # type: ignore[assignment]

    def add_piece(self, piece: Piece) -> None:
        """Register piece; called by Piece.attach() when piece.group is this Scene."""
        self._register(piece)

    @staticmethod
    def _set_facing(
        item: Piece | Group,
        facing: Literal["north", "south", "east", "west"],
    ) -> None:
        """Apply orientation to item's rotation field."""
        rot = orientation_to_rotation(facing)
        if isinstance(item, Group):
            item.local_rot = rot
        else:
            item.rotation = rot

    def _place_adjacent(
        self,
        item: Piece | Group,
        ref: Piece | Group,
        side: Literal["east", "west", "north", "south"],
    ) -> None:
        """Reposition item so it sits flush against ref on the given compass side."""
        origin, identity = _ORIGIN, _IDENTITY
        ref_bounds = self._bounds(ref, origin, identity)

        pos = item.position
        match side:
            case "east":
                item.position = Vector(ref_bounds.max_x, pos.y, pos.z)
            case "west":
                item_bounds = self._bounds(item, origin, identity)
                west_x = ref_bounds.min_x - (item_bounds.max_x - item_bounds.min_x)
                item.position = Vector(west_x, pos.y, pos.z)
            case "north":
                item.position = Vector(pos.x, pos.y, ref_bounds.max_z)
            case "south":
                item_bounds = self._bounds(item, origin, identity)
                south_z = ref_bounds.min_z - (item_bounds.max_z - item_bounds.min_z)
                item.position = Vector(pos.x, pos.y, south_z)

    def _traverse(
        self,
        item: Piece | Group,
        parent_pos: Vector,
        parent_rot: Matrix,
    ) -> Iterator[tuple[Piece, Vector, Matrix]]:
        """Recursively yield (piece, world_pos, world_rot) for every leaf Piece.

        Single recursive backbone used by _resolve, _bounds, and piece_at.
        """
        if isinstance(item, Group):
            world_pos = parent_pos + parent_rot * item.local_pos
            world_rot = parent_rot * item.local_rot
            for child in item.children:
                yield from self._traverse(child, world_pos, world_rot)
        else:
            yield (
                item,
                parent_pos + parent_rot * item.position,
                parent_rot * item.rotation,
            )

    def _bounds(
        self, item: Piece | Group, parent_pos: Vector, parent_rot: Matrix,
    ) -> _Bounds:
        """Compute the world-space axis-aligned bounding box of item and all descendants."""
        bounds = _Bounds()
        for piece, world_pos, world_rot in self._traverse(item, parent_pos, parent_rot):
            for xi, yi, zi in product((0, 1), repeat=3):
                bounds.expand(world_pos + world_rot * Vector(
                    xi * piece.ldu_x,
                    yi * piece.ldu_y,
                    zi * piece.ldu_z,
                ))
        return bounds

    # ------------------------------------------------------------------
    # Render pipeline
    # ------------------------------------------------------------------

    def render_str(self) -> str:
        """Render the scene to an LDraw string."""
        origin, identity = _ORIGIN, _IDENTITY
        return "\n".join(
            piece.render(world_pos, world_rot)
            for item in self.children
            for piece, world_pos, world_rot in self._traverse(item, origin, identity)
        )

    def render_file(self, file_path: Path | str) -> None:
        """Render the scene to an LDraw .mpd file."""
        Path(file_path).write_text(self.render_str())
