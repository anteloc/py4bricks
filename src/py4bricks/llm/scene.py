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

from pathlib import Path
from typing import TYPE_CHECKING, Literal

from py4bricks.geometry import Identity, Matrix, Vector
from py4bricks.llm.group import Group
from py4bricks.pieces import Piece

if TYPE_CHECKING:
    from collections.abc import Iterator


class Scene:
    """Root container for all Pieces and Groups in a model.

    All placement operations (place_at, attach_to) add their piece to the scene
    automatically — no manual add_piece() call required after placement.

    Rendering resolves the full Group transform chain lazily: structures can be
    repositioned or rotated after construction, and the output is always correct.
    """

    def __init__(self) -> None:
        self.children: list[Piece | Group] = []

        # Expose position/rotation so that Piece.__repr__ keeps working for pieces
        # whose .group is set to this scene (backward-compat duck-typing).
        self.position: Vector = Vector(0, 0, 0)
        self.rotation: Matrix = Identity()

    # ------------------------------------------------------------------
    # Tree mutation
    # ------------------------------------------------------------------

    def add(self, item: Piece | Group) -> None:
        """Add a Piece or Group to the scene."""
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
        side: Literal["back", "front", "right", "left"],
    ) -> Piece:
        """Attach piece to another piece on the given side and add it to the scene."""
        Piece.attach_to(piece=piece, to=to, side=side)
        self.add(piece)
        return piece

    # ------------------------------------------------------------------
    # Render pipeline
    # ------------------------------------------------------------------

    def _resolve(
        self,
        item: Piece | Group,
        parent_pos: Vector,
        parent_rot: Matrix,
    ) -> Iterator[str]:
        """Recursively resolve world-space transforms and yield LDraw lines.

        For each Group, composes its local transform with the inherited parent
        transform then recurses into children.  For each leaf Piece, calls
        Piece.render() with the fully-composed world-space position and rotation.
        """
        if isinstance(item, Group):
            world_pos = parent_pos + parent_rot * item.local_pos
            world_rot = parent_rot * item.local_rot
            for child in item.children:
                yield from self._resolve(child, world_pos, world_rot)
        else:
            # Piece: its .position/.rotation are already in the parent's local space
            world_pos = parent_pos + parent_rot * item.position
            world_rot = parent_rot * item.rotation
            yield item.render(world_pos, world_rot)

    def render_str(self) -> str:
        """Render the scene to an LDraw string."""
        origin   = Vector(0, 0, 0)
        identity = Identity()
        lines: list[str] = []
        for item in self.children:
            lines.extend(self._resolve(item, origin, identity))
        return "\n".join(lines)

    def render_file(self, file_path: Path | str) -> None:
        """Render the scene to an LDraw .mpd file."""
        Path(file_path).write_text(self.render_str())
