"""scene.py - LLM-friendly Scene: a named root Group that renders to LDraw.

Scene extends Group. Its local frame IS the world frame (origin, identity
rotation), so every placement/lookup verb inherited from Group — place_at,
place_on_top_of, place_adjacent_to, piece_at, remove_piece_at — operates in
world coordinates when called on the Scene.

On top of Group, Scene adds only rendering:
    * render_str()  — serialise the whole tree to an LDraw string
    * render_file() — write that string to a .mpd file

`0 // {name}` LDraw comments are emitted for the Scene and for every named
Group in the tree, making the output navigable and tying it back to the
semantic labels chosen by the LLM (e.g. "kitchen", "roof", "south_wall").

Coordinate conventions (same as Group/geometry.py):
    X — horizontal, positive to the right     (studs)
    Y — vertical,   positive upward           (plates)
    Z — depth,      positive towards the back (studs)
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from py4bricks.geometry import Identity, Matrix, Vector
from py4bricks.llm.group import Group

if TYPE_CHECKING:
    from collections.abc import Iterator

    from py4bricks.pieces import Piece


_ORIGIN:   Vector = Vector(0, 0, 0)
_IDENTITY: Matrix = Identity()


class Scene(Group):
    """The named root container; renders the whole tree to LDraw.

    Inherits every placement and lookup verb from Group. Because the Scene
    sits at origin with identity rotation, calling those verbs on it operates
    directly in world coordinates.
    """

    def __init__(self, name: str = "") -> None:
        super().__init__(name=name)

    def render_str(self) -> str:
        """Render the scene tree to an LDraw string with group-name comments."""
        lines: list[str] = []
        if self.name:
            lines.append(f"0 // {self.name}")
        for item in self.children:
            lines.extend(self._render_walk(item, _ORIGIN, _IDENTITY))
        return "\n".join(lines)

    def render_file(self, file_path: Path | str) -> None:
        """Render the scene to an LDraw .mpd file."""
        Path(file_path).write_text(self.render_str())

    def _render_walk(
        self,
        item: Piece | Group,
        parent_pos: Vector,
        parent_rot: Matrix,
    ) -> Iterator[str]:
        """Yield LDraw lines for item and its descendants, with group-name comments."""
        if isinstance(item, Group):
            world_pos = parent_pos + parent_rot * item.local_pos
            world_rot = parent_rot * item.local_rot
            if item.name:
                yield f"0 // {item.name}"
            for child in item.children:
                yield from self._render_walk(child, world_pos, world_rot)
        else:
            yield item.render(
                parent_pos + parent_rot * item.position,
                parent_rot * item.rotation,
            )
