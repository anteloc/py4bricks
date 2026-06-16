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
        keep_clear: set[tuple[int, int]] | None = None,
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
            door_span = _place_door(placed, entrance, door_colour or colour, leaf_colour or colour, keep_clear)
        if facade == "punched" and windows:
            _place_windows(placed, storeys, storey_height, window_colour or colour, door_span, keep_clear)
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
    keep_clear: set[tuple[int, int]] | None = None,
) -> tuple[Wall, int, int, int, int] | None:
    """Place a door on the widest exterior run, in the clear segment nearest the
    wall centre (avoiding partition junctions); return (wall, x0, x1, r0, r1)."""
    candidates = [(run, wall) for run, wall in placed if run[0] == facing]
    if not candidates:
        return None
    (run_facing, fixed, a0, a1), wall = max(candidates, key=lambda rw: rw[0][3] - rw[0][2])
    door = Door(colour=door_colour, leaf_colour=leaf_colour)
    dw, dh = door.opening_width_studs, door.opening_height_bricks
    if dh > wall._height_bricks:
        return None

    width = a1 - a0
    blocked = [
        (local - 1, local + 1)
        for local in _junction_locals(run_facing, fixed, a0, a1, keep_clear or set())
    ]
    centre = width / 2
    best_x: int | None = None
    for s0, s1 in _clear_segments(1, width - 1, blocked):
        if s1 - s0 < dw:
            continue
        x = max(s0, min(s1 - dw, round(centre - dw / 2)))
        if best_x is None or abs(x + dw / 2 - centre) < abs(best_x + dw / 2 - centre):
            best_x = x
    if best_x is None:
        return None
    wall.insert(piece=door, studs_x=best_x, brick_row=0)
    return wall, best_x, best_x + dw, 0, dh


def _place_windows(
    placed: list[tuple[tuple[Facing, int, int, int], Wall]],
    storeys: int,
    storey_height: int,
    colour: Colour,
    door_span: tuple[Wall, int, int, int, int] | None,
    keep_clear: set[tuple[int, int]] | None = None,
) -> None:
    """Distribute windows per storey, placed within the CLEAR segments of each run
    — the parts not blocked by the door or by a partition junction, so windows
    relocate around obstacles instead of just dropping out."""
    proto = Window(colour=colour)
    win_w, win_h = proto.opening_width_studs, proto.opening_height_bricks
    rows = [
        s * storey_height + max(1, (storey_height - win_h) // 2)
        for s in range(storeys)
    ]
    rows = [r for r in rows if r + win_h <= storeys * storey_height]

    for (facing, fixed, a0, a1), wall in placed:
        width = a1 - a0
        # Partition junctions on this run -> 2-stud-wide blocked intervals (local).
        junction_blocks = [
            (local - 1, local + 1)
            for local in _junction_locals(facing, fixed, a0, a1, keep_clear or set())
        ]
        for row in rows:
            blocked = list(junction_blocks)
            if door_span and wall is door_span[0]:
                _, dx0, dx1, dr0, dr1 = door_span
                if row < dr1 and dr0 < row + win_h:
                    blocked.append((dx0, dx1))
            for s0, s1 in _clear_segments(2, width - 2, blocked):
                for x in _even_in(s0, s1, win_w):
                    wall.insert(piece=Window(colour=colour, sill_colour=colour), studs_x=x, brick_row=row)


def _junction_locals(
    facing: Facing, fixed: int, a0: int, a1: int, junctions: set[tuple[int, int]],
) -> list[int]:
    """Wall-local stud positions of partition junctions that land on this run."""
    out: list[int] = []
    for jx, jz in junctions:
        if facing in ("south", "north") and jz == fixed:
            out.append(jx - a0 if facing == "south" else a1 - jx)
        elif facing in ("east", "west") and jx == fixed:
            out.append(jz - a0 if facing == "east" else a1 - jz)
    return out


def _clear_segments(lo: int, hi: int, blocked: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """[lo, hi] with the blocked intervals removed."""
    segments = [(lo, hi)]
    for b0, b1 in blocked:
        nxt: list[tuple[int, int]] = []
        for s0, s1 in segments:
            if b1 <= s0 or b0 >= s1:
                nxt.append((s0, s1))
                continue
            if s0 < b0:
                nxt.append((s0, b0))
            if b1 < s1:
                nxt.append((b1, s1))
        segments = nxt
    return segments


def _even_in(s0: int, s1: int, win_w: int) -> list[int]:
    """Evenly-spaced window left-edges inside a clear segment [s0, s1]."""
    width = s1 - s0
    if width < win_w:
        return []
    count = max(1, min(3, (width + 2) // (win_w + 2)))
    if count == 1:
        return [s0 + (width - win_w) // 2]
    step = (width - win_w) / (count - 1)
    return [int(round(s0 + i * step)) for i in range(count)]


def _overlaps(x0: int, x1: int, r0: int, r1: int, span: tuple[int, int, int, int]) -> bool:
    """True if (x0..x1, r0..r1) overlaps the door span (dx0, dx1, dr0, dr1)."""
    dx0, dx1, dr0, dr1 = span
    return x0 < dx1 and dx0 < x1 and r0 < dr1 and dr0 < r1


class FloorPlan:
    """A set of named room rectangles that tile a footprint.

    The exterior shell is just the union's boundary (use `footprint()`), while
    interior PARTITION walls fall on edges between two *different* rooms — the
    dual of the exterior tracer. Declare rooms like blocks, name them, and the
    engine derives all the internal walls:

        plan = (FloorPlan()
                .add_room(name="kitchen", x=0, z=0, width=8, length=6)
                .add_room(name="hall",    x=8, z=0, width=4, length=12)
                .add_room(name="living",  x=0, z=6, width=8, length=6))
        house = House.from_floor_plan(plan, palette=COTTAGE)
    """

    def __init__(self) -> None:
        self._rooms: list[tuple[str, int, int, int, int]] = []  # name, x, z, w, l

    def add_room(self, *, name: str, x: int, z: int, width: int, length: int) -> FloorPlan:
        """Add a named room rectangle; returns self for chaining."""
        self._rooms.append((name, x, z, width, length))
        return self

    def footprint(self) -> Footprint:
        """The union of all rooms, as a Footprint (for the exterior shell)."""
        fp = Footprint()
        for _, x, z, w, length in self._rooms:
            fp.add_block(x=x, z=z, width=w, length=length)
        return fp

    def _cell_rooms(self) -> dict[tuple[int, int], str]:
        out: dict[tuple[int, int], str] = {}
        for name, x, z, w, length in self._rooms:
            for cx in range(x, x + w):
                for cz in range(z, z + length):
                    out[(cx, cz)] = name
        return out

    def partition_runs(self) -> list[tuple[tuple[str, str], Facing, int, int, int]]:
        """Interior partition runs, one per ROOM-PAIR edge, as
        (pair, facing, fixed, a0, a1).

        `pair` is the two rooms a run separates (sorted). A vertical edge faces
        "east" at x=fixed; a horizontal one faces "north" at z=fixed; a0..a1 is
        the run's span on the other axis. Keying by pair keeps each wall a single
        room boundary, so a doorway in it connects exactly those two rooms.
        """
        rooms = self._cell_rooms()
        vertical: dict[tuple[tuple[str, str], int], set[int]] = defaultdict(set)
        horizontal: dict[tuple[tuple[str, str], int], set[int]] = defaultdict(set)
        for (cx, cz), room in rooms.items():
            west = rooms.get((cx - 1, cz))
            if west is not None and west != room:
                vertical[(tuple(sorted((room, west))), cx)].add(cz)
            south = rooms.get((cx, cz - 1))
            if south is not None and south != room:
                horizontal[(tuple(sorted((room, south))), cz)].add(cx)

        runs: list[tuple[tuple[str, str], Facing, int, int, int]] = []
        for (pair, x), czs in vertical.items():
            for a0, a1 in _merge_contiguous(czs):
                runs.append((pair, "east", x, a0, a1))
        for (pair, z), cxs in horizontal.items():
            for a0, a1 in _merge_contiguous(cxs):
                runs.append((pair, "north", z, a0, a1))
        return runs

    def partition_junctions(self) -> set[tuple[int, int]]:
        """World points where a partition END actually meets an exterior wall (the
        cell just beyond the end is outside the footprint). The exterior shell
        keeps windows clear of these — but only on the wall that's truly hit, so
        windows elsewhere are unaffected."""
        cells = set(self._cell_rooms())
        out: set[tuple[int, int]] = set()
        for _, facing, fixed, a0, a1 in self.partition_runs():
            if facing == "east":            # vertical partition at x=fixed
                if (fixed, a0 - 1) not in cells:
                    out.add((fixed, a0))
                if (fixed, a1) not in cells:
                    out.add((fixed, a1))
            else:                            # horizontal partition at z=fixed
                if (a0 - 1, fixed) not in cells:
                    out.add((a0, fixed))
                if (a1, fixed) not in cells:
                    out.add((a1, fixed))
        return out

    def build_partitions(
        self,
        *,
        height_bricks: int,
        colour: Colour,
        bonded: bool = True,
        doorways: bool = True,
        doorway_width: int = 3,
        name: str = "partitions",
    ) -> Group:
        """Build a Group of interior partition Walls (one storey high), with a
        centred doorway carved in each (so adjacent rooms connect).

        A partition's bricks render half a stud toward one end (low for vertical,
        high for horizontal walls), so the end that meets an EXTERIOR wall is
        trimmed one stud — it then stops exactly at the wall's inner face (a clean
        T-junction) instead of poking through it. Ends meeting other partitions
        are left full so they connect. A doorway is only carved where the wall is
        wide enough; a thin "corridor" room thus links every room it borders.
        """
        cells = set(self._cell_rooms())
        doorway_height = min(6, height_bricks - 1)
        partitions = Group(name=name)
        for _, facing, fixed, a0, a1 in self.partition_runs():
            if facing == "east" and (fixed, a0 - 1) not in cells:   # vertical: low end
                a0 += 1
            elif facing == "north" and (a1, fixed) not in cells:    # horizontal: high end
                a1 -= 1
            width = a1 - a0
            if width < 1:
                continue
            wall_facing, sx, sz = _wall_placement(facing, fixed, a0, a1)
            wall = Wall(width_studs=width, height_bricks=height_bricks, colour=colour, bonded=bonded)
            if doorways and width >= doorway_width + 2 and doorway_height >= 1:
                wall.opening(
                    studs_x=(width - doorway_width) // 2, brick_row=0,
                    width_studs=doorway_width, height_bricks=doorway_height,
                )
            partitions.place_at(wall, studs_x=sx, plates_y=0, studs_z=sz, facing=wall_facing)
        return partitions


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
