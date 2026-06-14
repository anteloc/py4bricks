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
from py4bricks.llm.openings import Door, Window
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
        self,
        *,
        height_bricks: int,
        colour: Colour,
        bonded: bool = True,
        windows: bool = False,
        window_colour: Colour | None = None,
        window_brick_row: int | None = None,
        entrance: Facing | None = None,
        door_colour: Colour | None = None,
        leaf_colour: Colour | None = None,
        name: str = "shell",
    ) -> Group:
        """Build a Group of exterior Walls covering the footprint boundary.

        Each run is placed exactly the way WallLayout/Box anchors a wall — at the
        edge's corner, with a rotation that runs the wall along the edge and its
        1-stud thickness inward. Corners overlap by a stud, the same as Box, so
        they read clean. Interior (shared) edges produce no run, so interiors
        stay continuous.

        Openings are optional and always EXTERIOR, since they can only attach to
        the exterior wall runs:
            windows  — distribute evenly-spaced windows along every wide-enough
                       run, with corner margins.
            entrance — put a door on the widest run facing this way; windows that
                       would clash with it are skipped.
        """
        runs = self.exterior_runs()
        shell = Group(name=name)
        placed: list[tuple[tuple[Facing, int, int, int], Wall]] = []
        for run in runs:
            facing, fixed, a0, a1 = run
            wall_facing, sx, sz = _wall_placement(facing, fixed, a0, a1)
            wall = Wall(width_studs=a1 - a0, height_bricks=height_bricks, colour=colour, bonded=bonded)
            shell.place_at(wall, studs_x=sx, plates_y=0, studs_z=sz, facing=wall_facing)
            placed.append((run, wall))

        door_span: tuple[Wall, int, int] | None = None
        if entrance is not None:
            door_span = _place_door(placed, entrance, door_colour or colour, leaf_colour or colour)
        if windows:
            _place_windows(placed, window_brick_row, height_bricks, window_colour or colour, door_span)
        return shell


def _even_positions(width: int, opening: int, margin: int = 2) -> list[int]:
    """Left-edge x of evenly-spaced openings across a run, with corner margins."""
    usable = width - 2 * margin
    if usable < opening:
        return []
    count = max(1, min(4, (usable + 3) // (opening + 3)))
    if count == 1:
        return [margin + (usable - opening) // 2]
    step = (usable - opening) / (count - 1)
    return [int(round(margin + i * step)) for i in range(count)]


def _place_door(
    placed: list[tuple[tuple[Facing, int, int, int], Wall]],
    facing: Facing,
    door_colour: Colour,
    leaf_colour: Colour,
) -> tuple[Wall, int, int] | None:
    """Place a centred door on the widest exterior run with the given facing."""
    candidates = [(run, wall) for run, wall in placed if run[0] == facing]
    if not candidates:
        return None
    (_, _, a0, a1), wall = max(candidates, key=lambda rw: rw[0][3] - rw[0][2])
    door = Door(colour=door_colour, leaf_colour=leaf_colour)
    if door.opening_height_bricks > wall._height_bricks:
        return None
    x = max(0, ((a1 - a0) - door.opening_width_studs) // 2)
    wall.insert(piece=door, studs_x=x, brick_row=0)
    return wall, x, x + door.opening_width_studs


def _place_windows(
    placed: list[tuple[tuple[Facing, int, int, int], Wall]],
    brick_row: int | None,
    height_bricks: int,
    colour: Colour,
    door_span: tuple[Wall, int, int] | None,
) -> None:
    """Distribute windows along every run, skipping any clash with the door."""
    proto = Window(colour=colour)
    win_w, win_h = proto.opening_width_studs, proto.opening_height_bricks
    row = brick_row if brick_row is not None else max(1, (height_bricks - win_h) // 2)
    if row + win_h > height_bricks:
        return
    for (_, _, a0, a1), wall in placed:
        for x in _even_positions(a1 - a0, win_w):
            if door_span and wall is door_span[0] and not (x + win_w <= door_span[1] or x >= door_span[2]):
                continue
            wall.insert(piece=Window(colour=colour, sill_colour=colour), studs_x=x, brick_row=row)


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
