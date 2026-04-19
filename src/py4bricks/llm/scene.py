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
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from py4bricks.geometry import (
    Identity,
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

    All placement operations (place_at, attach_to) add their piece to the scene
    automatically — no manual add_piece() call required after placement.

    Rendering resolves the full Group transform chain lazily: structures can be
    repositioned or rotated after construction, and the output is always correct.
    """

    def __init__(self) -> None:
        self.children: list[Piece | Group] = []

        # Expose position/rotation so Piece.__repr__ keeps working for pieces
        # whose .group is set to this scene (backward-compat duck-typing).
        self.position: Vector = Vector(0, 0, 0)
        self.rotation: Matrix = Identity()

    # ------------------------------------------------------------------
    # Tree mutation
    # ------------------------------------------------------------------

    def add(
        self,
        item: Piece | Group,
        *,
        facing: Literal["north", "south", "east", "west"] | None = None,
        adjacent_to: Piece | Group | None = None,
        side: Literal["east", "west", "north", "south"] | None = None,
        on_top_of: Piece | Group | None = None,
    ) -> None:
        """Add a Piece or Group to the scene, optionally repositioning it.

        facing       — set the item's orientation before adding.
        adjacent_to  — place item flush against the given reference on the
                       given compass side (requires side=).
        on_top_of    — place item flush on top of the given reference.

        Relational kwargs only set the relevant axis; the LLM controls the
        remaining axes via the item's own studs_x / plates_y / studs_z.
        facing= may be combined with adjacent_to= or on_top_of=.
        """
        if facing is not None:
            rot = orientation_to_rotation(facing)
            if isinstance(item, Group):
                item.local_rot = rot
            else:
                item.rotation = rot

        if adjacent_to is not None:
            if side is None:
                raise ValueError("adjacent_to= requires side=")
            self._place_adjacent(item, ref=adjacent_to, side=side)

        if on_top_of is not None:
            ref_bounds = self._bounds(on_top_of)
            self._set_pos(item, y=ref_bounds.max_y)

        self.children.append(item)
        if isinstance(item, Piece):
            item.group = self  # type: ignore[assignment]  — duck-typed for backward compat

    def add_piece(self, piece: Piece) -> None:
        """Add a Piece to the scene. Kept for backward compatibility."""
        self.add(piece)

    # ------------------------------------------------------------------
    # Placement helpers (absolute and relative)
    # ------------------------------------------------------------------

    def place_at(
        self,
        piece: Piece,
        studs_x: int,
        plates_y: int,
        studs_z: int,
        orientation: Literal["north", "south", "east", "west"] = "north",
    ) -> Piece:
        """Place piece at the given grid coordinates and add it to the scene."""
        Piece.place_at(
            piece=piece,
            studs_x=studs_x,
            plates_y=plates_y,
            studs_z=studs_z,
            orientation=orientation,
        )
        self.add(piece)
        return piece

    def attach_to(
        self,
        piece: Piece,
        to: Piece,
        side: Literal["front", "back", "left", "right", "top", "bottom"],
        orientation: Literal["north", "south", "east", "west"] | None = None,
        right_studs: int = 0,
        back_studs: int = 0,
    ) -> Piece:
        """Attach piece to another piece on the given side and add it to the scene.

        orientation overrides the attached piece's facing; None inherits to's.
        right_studs / back_studs are only meaningful for side="top" or "bottom".
        """
        Piece.attach_to(
            piece=piece, to=to, side=side,
            orientation=orientation,
            right_studs=right_studs, back_studs=back_studs,
        )
        self.add(piece)
        return piece

    def piece_at(
        self,
        studs_x: int,
        plates_y: int,
        studs_z: int,
    ) -> Piece | None:
        """Return the first Piece whose world-space origin matches the given grid position.

        Traverses the full tree lazily. Returns None if no match is found.
        """
        target = Vector(studs_to_ldu(studs_x), plates_to_ldu(plates_y), studs_to_ldu(studs_z))
        origin, identity = Vector(0, 0, 0), Identity()
        for item in self.children:
            for piece, world_pos, _ in self._traverse(item, origin, identity):
                if (abs(world_pos.x - target.x) < _POSITION_TOLERANCE
                        and abs(world_pos.y - target.y) < _POSITION_TOLERANCE
                        and abs(world_pos.z - target.z) < _POSITION_TOLERANCE):
                    return piece
        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_pos(item: Piece | Group) -> Vector:
        return item.local_pos if isinstance(item, Group) else item.position

    @staticmethod
    def _set_pos(
        item: Piece | Group,
        x: float | None = None,
        y: float | None = None,
        z: float | None = None,
    ) -> None:
        """Replace one or more axes of item's position, leaving the rest unchanged."""
        pos = item.local_pos if isinstance(item, Group) else item.position
        new_pos = Vector(
            x if x is not None else pos.x,
            y if y is not None else pos.y,
            z if z is not None else pos.z,
        )
        if isinstance(item, Group):
            item.local_pos = new_pos
        else:
            item.position = new_pos

    def _place_adjacent(
        self,
        item: Piece | Group,
        ref: Piece | Group,
        side: Literal["east", "west", "north", "south"],
    ) -> None:
        """Reposition item so it sits flush against ref on the given compass side."""
        origin, identity = Vector(0, 0, 0), Identity()
        ref_bounds = self._bounds(ref, origin, identity)

        match side:
            case "east":
                self._set_pos(item, x=ref_bounds.max_x)
            case "west":
                item_bounds = self._bounds(item, origin, identity)
                self._set_pos(item, x=ref_bounds.min_x - (item_bounds.max_x - item_bounds.min_x))
            case "north":
                self._set_pos(item, z=ref_bounds.max_z)
            case "south":
                item_bounds = self._bounds(item, origin, identity)
                self._set_pos(item, z=ref_bounds.min_z - (item_bounds.max_z - item_bounds.min_z))

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
        self,
        item: Piece | Group,
        parent_pos: Vector | None = None,
        parent_rot: Matrix | None = None,
    ) -> _Bounds:
        """Compute the world-space axis-aligned bounding box of item and all descendants."""
        bounds = _Bounds()
        for piece, world_pos, world_rot in self._traverse(
            item,
            parent_pos or Vector(0, 0, 0),
            parent_rot or Identity(),
        ):
            for xi, yi, zi in [(x, y, z) for x in (0, 1) for y in (0, 1) for z in (0, 1)]:
                bounds.expand(world_pos + world_rot * Vector(
                    xi * piece.ldu_x,
                    yi * piece.ldu_y,
                    zi * piece.ldu_z,
                ))
        return bounds

    # ------------------------------------------------------------------
    # Render pipeline
    # ------------------------------------------------------------------

    def _resolve(
        self,
        item: Piece | Group,
        parent_pos: Vector,
        parent_rot: Matrix,
    ) -> Iterator[str]:
        """Yield LDraw type-1 lines for item and all its descendants."""
        for piece, world_pos, world_rot in self._traverse(item, parent_pos, parent_rot):
            yield piece.render(world_pos, world_rot)

    def render_str(self) -> str:
        """Render the scene to an LDraw string."""
        origin, identity = Vector(0, 0, 0), Identity()
        lines: list[str] = []
        for item in self.children:
            lines.extend(self._resolve(item, origin, identity))
        return "\n".join(lines)

    def render_file(self, file_path: Path | str) -> None:
        """Render the scene to an LDraw .mpd file."""
        Path(file_path).write_text(self.render_str())
