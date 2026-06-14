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
from typing import TYPE_CHECKING, Literal

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

    @property
    def blocks(self) -> list[tuple[int, int, int, int]]:
        """The blocks as (x, z, width, length) tuples — e.g. for per-block roofs."""
        return list(self._rects)

    def inset(self, margin: int) -> Footprint:
        """A copy with every block shrunk by `margin` studs on all sides — used
        to step a tier back from the one below. Blocks too small to survive the
        inset are dropped."""
        out = Footprint()
        for x, z, w, length in self._rects:
            if w - 2 * margin >= 1 and length - 2 * margin >= 1:
                out.add_block(x=x + margin, z=z + margin, width=w - 2 * margin, length=length - 2 * margin)
        return out

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
        storeys: int = 1,
        foundation_colour: Colour | None = None,
        coping_colour: Colour | None = None,
        band_colour: Colour | None = None,
        mottle_colour: Colour | None = None,
        mottle_ratio: float = 0.12,
        facade: Literal["punched", "curtain"] = "punched",
        windows: bool = False,
        window_colour: Colour | None = None,
        glass_colour: Colour | None = None,
        glass_segment_width: int = 2,
        glass_segment_height: int = 2,
        entrance: Facing | None = None,
        door_colour: Colour | None = None,
        leaf_colour: Colour | None = None,
        exclude_under: set[tuple[int, int]] | None = None,
        name: str = "shell",
    ) -> Group:
        """Build a Group of exterior Walls covering the footprint boundary.

        Each run is placed exactly the way WallLayout/Box anchors a wall — at the
        edge's corner, with a rotation that runs the wall along the edge and its
        1-stud thickness inward. Corners overlap by a stud, the same as Box, so
        they read clean. Interior (shared) edges produce no run, so interiors
        stay continuous.

        Every run is enriched uniformly (foundation course, coping cap, floor-line
        bands between storeys, mottled texture) so the whole shell reads as one
        building. With `storeys > 1`, a string course is added at each floor line
        and windows are placed per storey (centred within each), so they never
        clip the bands.

        A "punched" facade gets individual windows (houses); a "curtain" facade
        gets a uniform glazed grid — trans glass framed by mullions/transoms, no
        floor bands (they would beat against the transom grid). Either way
        openings stay EXTERIOR, since they only attach to the exterior runs.

        `exclude_under` (a set of covered cells) drops any run segment whose
        interior cell is covered — used to build a tier's parapet only along the
        exposed terrace edges, never where the tier above continues straight up.
        """
        storey_height = height_bricks // max(1, storeys)
        # Curtain walls use the transom grid for horizontal lines; floor bands
        # would beat against it and look irregular, so omit them there.
        floor_lines = [] if facade == "curtain" else [s * storey_height for s in range(1, storeys)]

        runs = self.exterior_runs()
        shell = Group(name=name)
        placed: list[tuple[tuple[Facing, int, int, int], Wall]] = []

        def make_wall(facing: Facing, fixed: int, s0: int, s1: int) -> None:
            wall_facing, sx, sz = _wall_placement(facing, fixed, s0, s1)
            wall = Wall(width_studs=s1 - s0, height_bricks=height_bricks, colour=colour, bonded=bonded)
            if foundation_colour is not None:
                wall.foundation(colour=foundation_colour)
            if coping_colour is not None:
                wall.coping(colour=coping_colour)
            for row in floor_lines:
                wall.band(brick_row=row, colour=band_colour or coping_colour or colour)
            if mottle_colour is not None:
                wall.mottle(colour=mottle_colour, ratio=mottle_ratio)
            if facade == "curtain":
                wall.glaze(
                    glass_colour=glass_colour or colour, mullion_colour=window_colour or colour,
                    segment_width_studs=glass_segment_width, segment_height_bricks=glass_segment_height,
                )
            shell.place_at(wall, studs_x=sx, plates_y=0, studs_z=sz, facing=wall_facing)
            placed.append(((facing, fixed, s0, s1), wall))

        for facing, fixed, a0, a1 in runs:
            if exclude_under is None:
                make_wall(facing, fixed, a0, a1)   # full run; calibrated anchors tile corners cleanly
                continue
            # Parapet case: drop segments the tier above sits on.
            def covered(along: int, facing: Facing = facing, fixed: int = fixed) -> bool:
                return _interior_cell(facing, fixed, along) in exclude_under
            for s0, s1 in _split_runs(a0, a1, covered):
                make_wall(facing, fixed, s0, s1)

        door_span: tuple[Wall, int, int, int, int] | None = None
        if entrance is not None:
            door_span = _place_door(placed, entrance, door_colour or colour, leaf_colour or colour)
        if facade == "punched" and windows:
            _place_windows(placed, storeys, storey_height, window_colour or colour, door_span)
        return shell


def _split_runs(a0: int, a1: int, excluded) -> list[tuple[int, int]]:
    """Contiguous [start, end) sub-runs of [a0, a1) whose positions are not excluded."""
    out: list[tuple[int, int]] = []
    start: int | None = None
    for v in range(a0, a1):
        if excluded(v):
            if start is not None:
                out.append((start, v))
                start = None
        elif start is None:
            start = v
    if start is not None:
        out.append((start, a1))
    return out


def _interior_cell(facing: Facing, fixed: int, along: int) -> tuple[int, int]:
    """The occupied cell just inside an exterior edge run at position `along`."""
    if facing == "north":
        return along, fixed - 1
    if facing == "south":
        return along, fixed
    if facing == "east":
        return fixed - 1, along
    return fixed, along  # west


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
) -> tuple[Wall, int, int, int, int] | None:
    """Place a centred door on the widest exterior run; return its (wall, x0, x1, r0, r1)."""
    candidates = [(run, wall) for run, wall in placed if run[0] == facing]
    if not candidates:
        return None
    (_, _, a0, a1), wall = max(candidates, key=lambda rw: rw[0][3] - rw[0][2])
    door = Door(colour=door_colour, leaf_colour=leaf_colour)
    if door.opening_height_bricks > wall._height_bricks:
        return None
    x = max(0, ((a1 - a0) - door.opening_width_studs) // 2)
    wall.insert(piece=door, studs_x=x, brick_row=0)
    return wall, x, x + door.opening_width_studs, 0, door.opening_height_bricks


def _place_windows(
    placed: list[tuple[tuple[Facing, int, int, int], Wall]],
    storeys: int,
    storey_height: int,
    colour: Colour,
    door_span: tuple[Wall, int, int, int, int] | None,
) -> None:
    """Place windows per storey (centred within each), skipping clashes with the door."""
    proto = Window(colour=colour)
    win_w, win_h = proto.opening_width_studs, proto.opening_height_bricks
    rows = [
        s * storey_height + max(1, (storey_height - win_h) // 2)
        for s in range(storeys)
    ]
    rows = [r for r in rows if r + win_h <= storeys * storey_height]

    for (_, _, a0, a1), wall in placed:
        for row in rows:
            for x in _even_positions(a1 - a0, win_w):
                if door_span and wall is door_span[0] and _overlaps(
                    x, x + win_w, row, row + win_h, door_span[1:],
                ):
                    continue
                wall.insert(piece=Window(colour=colour, sill_colour=colour), studs_x=x, brick_row=row)


def _overlaps(x0: int, x1: int, r0: int, r1: int, span: tuple[int, int, int, int]) -> bool:
    """True if (x0..x1, r0..r1) overlaps the door span (dx0, dx1, dr0, dr1)."""
    dx0, dx1, dr0, dr1 = span
    return x0 < dx1 and dx0 < x1 and r0 < dr1 and dr0 < r1


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
