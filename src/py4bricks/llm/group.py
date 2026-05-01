"""group.py - LLM-friendly hierarchical Group: placement, lookup, traversal.

A Group holds Pieces and sub-Groups in its own local coordinate system.
Every placement verb (place, place_at, place_on_top_of, place_adjacent_to)
and every lookup verb (piece_at, remove_piece_at) operates in THIS Group's
local frame, so LLM-generated scripts compose naturally:

    def make_room(room_name):
        room = Group(name=room_name)
        room.place_at(make_wall("north"), studs_x=0, plates_y=0, studs_z=0)
        room.place_adjacent_to(make_wall("east"), ref=..., side="east")
        return room

Scene subclasses Group as the named root whose local frame IS the world.

Transforms are composed recursively at render time:
    world_pos = parent_pos + parent_rot * local_pos
    world_rot = parent_rot * local_rot

LLM-generated scripts never perform position arithmetic or unit conversions
directly: pass `studs_x`, `plates_y`, `studs_z`, and `facing` — the Group
converts to internal Vector/Matrix.
"""
from __future__ import annotations

import copy
from dataclasses import InitVar, dataclass, field
from itertools import product
from typing import TYPE_CHECKING

from py4bricks.geometry import (
    Axis,
    LDU_PER_STUD_HEIGHT,
    Identity,
    Matrix,
    Vector,
    XAxis,
    YAxis,
    ZAxis,
    ldu_to_plates,
    ldu_to_studs,
    orientation_to_rotation,
    plates_to_ldu,
    studs_to_ldu,
)
from py4bricks.pieces import Piece

if TYPE_CHECKING:
    from collections.abc import Iterator

    from py4bricks.llm.types import Facing, Side

# Half an LDU — smaller than any grid step; used for position matching.
_POSITION_TOLERANCE: float = 0.5

_ORIGIN:   Vector = Vector(0, 0, 0)
_IDENTITY: Matrix = Identity()

# Reflection matrices keyed by the normal axis of the mirror plane.
_REFLECTION: dict[type[Axis], Matrix] = {
    XAxis: Matrix([[-1, 0, 0], [0, 1, 0], [0, 0, 1]]),
    YAxis: Matrix([[1, 0, 0], [0, -1, 0], [0, 0, 1]]),
    ZAxis: Matrix([[1, 0, 0], [0, 1, 0], [0, 0, -1]]),
}


def _reflect_children(children: list, R: Matrix) -> None:
    """Recursively apply reflection matrix R to all positions and rotations in the subtree."""
    for child in children:
        child.position = R * child.position
        child.rotation = R * child.rotation * R
        if isinstance(child, Group):
            _reflect_children(child.children, R)


@dataclass
class _Bounds:
    """Axis-aligned bounding box, accumulated during tree traversal."""

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


@dataclass(kw_only=True)
class Group:
    """A hierarchical container with a local coordinate system.

    Position is given in studs (X/Z) and plates (Y); orientation as a compass
    direction. The Group converts these to internal Vector/Matrix on construction,
    so LLM-generated scripts stay free of numeric conversions.

    The optional `name` is a semantic label (e.g. "kitchen", "roof"). When set,
    it is emitted as an LDraw `0 // {name}` comment at render time, making the
    output navigable and matching the `make_room(name)` factory idiom.

    Children can be Piece instances or nested Groups. Placement verbs position
    items in THIS Group's local frame; lookup verbs search its subtree.

    Scene subclasses Group as the named root whose local frame IS the world.

    Prefer named proportions to magic numbers when computing coordinates:

        from py4bricks.llm import proportional
        wall.place_at(
            door,
            studs_x=proportional(WALL_LENGTH, (1, 2)),   # centred
            plates_y=0, studs_z=0,
        )
    """

    name:          str = ""
    at_studs_x:    InitVar[int] = 0
    at_plates_y:   InitVar[int] = 0
    at_studs_z:    InitVar[int] = 0
    orientation:   InitVar[Facing] = "north"
    children:      list[Piece | Group] = field(default_factory=list)

    # Derived in __post_init__; used by _traverse() and by Piece.__repr__.
    local_pos: Vector = field(init=False)
    local_rot: Matrix = field(init=False)

    def __post_init__(
        self,
        at_studs_x: int,
        at_plates_y: int,
        at_studs_z: int,
        orientation: Facing,
    ) -> None:
        self.local_pos = Vector(
            x=studs_to_ldu(at_studs_x),
            y=plates_to_ldu(at_plates_y),
            z=studs_to_ldu(at_studs_z),
        )
        self.local_rot = orientation_to_rotation(orientation)

    # ------------------------------------------------------------------
    # Duck-type surface for Piece.__repr__ and Piece.attach()
    # ------------------------------------------------------------------

    @property
    def position(self) -> Vector:
        """Local position; duck-types Piece.position for uniform treatment."""
        return self.local_pos

    @position.setter
    def position(self, value: Vector) -> None:
        self.local_pos = value

    @property
    def rotation(self) -> Matrix:
        """Local rotation; duck-types Piece.rotation so Piece.__repr__ works."""
        return self.local_rot

    @rotation.setter
    def rotation(self, value: Matrix) -> None:
        self.local_rot = value

    @property
    def studs_x(self) -> int:
        """Bounding box width of all children, in studs."""
        if not self.children:
            return 0
        b = self._bounds(self, _ORIGIN, _IDENTITY)
        return ldu_to_studs(b.max_x - b.min_x)

    @property
    def plates_y(self) -> int:
        """Bounding box height of all children, in plates."""
        if not self.children:
            return 0
        b = self._bounds(self, _ORIGIN, _IDENTITY)
        return ldu_to_plates(b.max_y - b.min_y)

    @property
    def studs_z(self) -> int:
        """Bounding box depth of all children, in studs."""
        if not self.children:
            return 0
        b = self._bounds(self, _ORIGIN, _IDENTITY)
        return ldu_to_studs(b.max_z - b.min_z)

    # ------------------------------------------------------------------
    # Container ops
    # ------------------------------------------------------------------

    def add(self, item: Piece | Group) -> Group:
        """Add a Piece or sub-Group as-is (no placement change). Returns self."""
        self._register(item)
        return self

    def copy(self) -> Group:
        """Return a deep copy of this Group and all its descendants."""
        return copy.deepcopy(self)

    def mirror_along_plane(self, plane: tuple[type[Axis], type[Axis]]) -> Group:
        """Return a mirrored deep copy of this Group.

        The mirror plane is defined by two axes, e.g. (XAxis, ZAxis) mirrors
        across the floor (negates Y), (YAxis, ZAxis) mirrors left-to-right
        (negates X).  Positions and rotations of every piece and sub-group are
        reflected correctly, preserving valid rotation matrices.
        """
        normal = ({XAxis, YAxis, ZAxis} - set(plane)).pop()
        R = _REFLECTION[normal]
        mirrored = self.copy()
        _reflect_children(mirrored.children, R)
        return mirrored

    def _adopt(self, piece: Piece) -> None:
        """Duck-type hook for Piece.__init__() and Piece.attach().

        Prefer `add()` or the placement verbs in LLM-facing code; this exists
        so that `Piece(group=g)` and `piece.attach(...)` auto-register without
        forcing callers to call add() explicitly.
        """
        self._register(piece)

    # ------------------------------------------------------------------
    # Placement — all operate in THIS Group's local frame
    # ------------------------------------------------------------------

    def place_at(
        self,
        item: Piece | Group,
        *,
        studs_x: int = 0,
        plates_y: int = 0,
        studs_z: int = 0,
        facing: Facing = "north",
    ) -> Piece | Group:
        """Place item at local grid coordinates (studs_x, plates_y, studs_z).

        All coordinates default to 0, so `group.place_at(item)` drops item at
        the Group's local origin — the "add this whole pre-built structure"
        case. Pass any subset of coordinates to offset.
        """
        item.position = Vector(
            studs_to_ldu(studs_x),
            plates_to_ldu(plates_y),
            studs_to_ldu(studs_z),
        )
        self._set_facing(item, facing)
        self._register(item)
        return item

    def place_on_top_of(
        self,
        item: Piece | Group,
        ref: Piece | Group,
        *,
        right_studs: int = 0,
        back_studs: int = 0,
        facing: Facing = "north",
    ) -> Piece | Group:
        """Stack item flush on top of ref, optionally offset by studs.

        right_studs — shift item to the right (positive X) by this many studs.
        back_studs  — shift item towards the back (positive Z) by this many studs.

        ref must be a direct child of this Group.
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
        side: Side,
        facing: Facing = "north",
    ) -> Piece | Group:
        """Place item flush against ref on the given compass side.

        ref must be a direct child of this Group.
        """
        self._place_adjacent(item, ref=ref, side=side)
        self._set_facing(item, facing)
        self._register(item)
        return item

    # ------------------------------------------------------------------
    # Lookup — searches THIS Group's subtree
    # ------------------------------------------------------------------

    def piece_at(
        self, *, studs_x: int, plates_y: int, studs_z: int,
    ) -> Piece | None:
        """Return the first Piece whose composed position matches the given local coords."""
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
                for piece, local_pos, _ in self._traverse(item, _ORIGIN, _IDENTITY)
                if _near(local_pos)
            ),
            None,
        )

    def remove_piece_at(
        self, *, studs_x: int, plates_y: int, studs_z: int,
    ) -> Piece | None:
        """Remove and return the Piece at the given local coords, or None.

        The piece is removed from its immediate parent container — which may
        be this Group or any nested sub-Group.
        """
        piece = self.piece_at(studs_x=studs_x, plates_y=plates_y, studs_z=studs_z)
        if piece is None:
            return None
        if piece.group is not None:
            piece.group.children.remove(piece)
        piece.group = None
        return piece

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _register(self, item: Piece | Group) -> None:
        """Append item to children; set piece.group so Piece.attach() auto-registers."""
        self.children.append(item)
        if isinstance(item, Piece):
            item.group = self  # type: ignore[assignment]  — duck-typed

    def _set_facing(
        self,
        item: Piece | Group,
        facing: Facing,
    ) -> None:
        """Apply orientation to item's rotation (Piece and Group uniformly)."""
        item.rotation = orientation_to_rotation(facing)

    def _place_adjacent(
        self,
        item: Piece | Group,
        ref: Piece | Group,
        side: Side,
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
        """Yield (piece, composed_pos, composed_rot) for every leaf Piece.

        Single recursive backbone used by _bounds, piece_at, and Scene.render_str.
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
        """Axis-aligned bounding box of item and all descendants, in this Group's frame."""
        bounds = _Bounds()
        for piece, pos, rot in self._traverse(item, parent_pos, parent_rot):
            for xi, yi, zi in product((0, 1), repeat=3):
                bounds.expand(pos + rot * Vector(
                    xi * piece.ldu_x,
                    yi * piece.ldu_y,
                    zi * piece.ldu_z,
                ))
        return bounds
