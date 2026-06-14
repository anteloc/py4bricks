"""footprint.py — compose a building from rectangles; derive its wall shell.

The LLM declares a building's footprint as a union of rectangular blocks (in
studs). The boundary tracer then builds walls ONLY along the exterior edges:
edges shared between two blocks are interior and get no wall, so the interiors
are continuous by construction. This is the composable basis for any massing
(L / T / U / courtyard / wings / bays) with no per-shape special-casing.

    plan = Footprint()
    plan.add_block(x=0,  z=0, width=20, length=16)   # main
    plan.add_block(x=20, z=4, width=12, length=12)   # wing  -> L-plan
    shell = plan.build_shell(height_bricks=9, colour=Light_Bluish_Grey)

Coordinate conventions (studs): X east(+)/west(-), Z north(+)/south(-).
A block at (x, z, width, length) occupies the unit cells
    cx in [x, x+width), cz in [z, z+length)
i.e. world extent x[x, x+width], z[z, z+length].
"""
from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py4bricks.colour import Colour
    from py4bricks.llm.types import Facing

from py4bricks.llm.group import Group
from py4bricks.llm.wall import Wall


class Footprint:
    """A union of rectangular blocks, in studs, that yields a wall shell."""

    def __init__(self) -> None:
        self._rects: list[tuple[int, int, int, int]] = []  # (x, z, width, length)

    def add_block(self, *, x: int, z: int, width: int, length: int) -> Footprint:
        """Add a rectangular block; returns self for chaining."""
        self._rects.append((x, z, width, length))
        return self

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------

    def cells(self) -> set[tuple[int, int]]:
        """The set of occupied unit cells (the union of all blocks)."""
        out: set[tuple[int, int]] = set()
        for x, z, w, length in self._rects:
            for cx in range(x, x + w):
                for cz in range(z, z + length):
                    out.add((cx, cz))
        return out

    def exterior_runs(self) -> list[tuple[Facing, int, int, int]]:
        """Merged exterior wall runs as (facing, fixed, along0, along1).

        `facing` is the outward normal; `fixed` is the edge's constant coord
        (z for north/south runs, x for east/west); along0..along1 is the run's
        world span on the other axis. Edges between two occupied cells are
        interior and excluded.
        """
        cells = self.cells()
        # outward facing -> {fixed_coord: set(along_coords)}
        edges: dict[Facing, dict[int, set[int]]] = {
            "north": defaultdict(set), "south": defaultdict(set),
            "east": defaultdict(set),  "west": defaultdict(set),
        }
        for cx, cz in cells:
            if (cx, cz + 1) not in cells:
                edges["north"][cz + 1].add(cx)   # top face, exterior +Z
            if (cx, cz - 1) not in cells:
                edges["south"][cz].add(cx)        # bottom face, exterior -Z
            if (cx + 1, cz) not in cells:
                edges["east"][cx + 1].add(cz)     # right face, exterior +X
            if (cx - 1, cz) not in cells:
                edges["west"][cx].add(cz)         # left face, exterior -X

        runs: list[tuple[Facing, int, int, int]] = []
        for facing, by_fixed in edges.items():
            for fixed, alongs in by_fixed.items():
                for a0, a1 in _merge_contiguous(alongs):
                    runs.append((facing, fixed, a0, a1))
        return runs

    # ------------------------------------------------------------------
    # Shell
    # ------------------------------------------------------------------

    def build_shell(
        self, *, height_bricks: int, colour: Colour, bonded: bool = True, name: str = "shell",
    ) -> Group:
        """Build a Group of exterior Walls covering the footprint boundary.

        Each run is placed exactly the way WallLayout/Box anchors a wall — at the
        edge's corner, with a rotation that runs the wall along the edge and its
        1-stud thickness inward. Corners overlap by a stud, the same as Box, so
        they read clean. Interior (shared) edges produce no run, so interiors
        stay continuous.
        """
        shell = Group(name=name)
        for facing, fixed, a0, a1 in self.exterior_runs():
            wall_facing, sx, sz = _wall_placement(facing, fixed, a0, a1)
            wall = Wall(width_studs=a1 - a0, height_bricks=height_bricks, colour=colour, bonded=bonded)
            shell.place_at(wall, studs_x=sx, plates_y=0, studs_z=sz, facing=wall_facing)
        return shell


def _merge_contiguous(values: set[int]) -> list[tuple[int, int]]:
    """Merge sorted integers into [start, end) runs of consecutive cells."""
    out: list[tuple[int, int]] = []
    for v in sorted(values):
        if out and v == out[-1][1]:
            out[-1] = (out[-1][0], v + 1)
        else:
            out.append((v, v + 1))
    return out


def _wall_placement(facing: Facing, fixed: int, a0: int, a1: int) -> tuple[Facing, int, int]:
    """(wall_facing, studs_x, studs_z) replicating WallLayout's wall anchoring.

    `facing` is the edge's OUTWARD normal; the returned `wall_facing` is the
    travel-direction rotation WallLayout uses, which runs the wall along the
    edge and pushes its 1-stud thickness inward. Anchoring at the edge corner
    (not an interior cell) is what makes the render line up — unlike anchoring
    by logical cell, which ignores Wall's rotation-dependent render offset.
    """
    if facing == "south":   # bottom edge, interior is +Z  -> identity
        return "north", a0, fixed
    if facing == "north":   # top edge, interior is -Z      -> 180°
        return "south", a1, fixed
    if facing == "east":    # right edge, interior is -X     -> 270°
        return "west", fixed, a0
    return "east", fixed, a1  # left edge, interior is +X    -> 90°
